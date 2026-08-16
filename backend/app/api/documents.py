from uuid import UUID
import io

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.deps import require_permission
from app.db.session import get_db

from app.models.document import (
    Document,
    DocumentVersion,
    EncryptionKey,
)
from app.models.user import User

from app.storage.local import LocalStorage

from app.crypto.base import EncryptedBlob
from app.crypto.aes_service import encrypt_file
from app.crypto.decrypt_service import decrypt_file
from app.crypto.master_key import get_master_key
from app.crypto.hashing import sha256_hex


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


# ============================================================
# Storage
# ============================================================

storage = LocalStorage("./storage")


# ============================================================
# Upload validation
# ============================================================

MAX_SIZE = 50 * 1024 * 1024  # 50 MB

ALLOWED_MIME = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/msword",
}


# ============================================================
# Request schemas
# ============================================================

class DocumentUpdateIn(BaseModel):
    filename: str | None = None


# ============================================================
# Helper
# ============================================================

def _get_owned_or_404(
    db: Session,
    doc_id: UUID,
    current_user: User,
) -> Document:

    doc = (
        db.query(Document)
        .filter(
            Document.id == doc_id,
            Document.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return doc


# ============================================================
# Upload document
# ============================================================

@router.post(
    "",
    dependencies=[
        Depends(
            require_permission("document:create")
        )
    ],
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # --------------------------------------------------------
    # Validate MIME type
    # --------------------------------------------------------

    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}",
        )

    # --------------------------------------------------------
    # Read file
    # --------------------------------------------------------

    data = await file.read()

    # --------------------------------------------------------
    # Validate file size
    # --------------------------------------------------------

    if len(data) > MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 50 MB.",
        )

    if len(data) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # --------------------------------------------------------
    # Calculate SHA-256 hash
    #
    # This happens before encryption so the hash represents
    # the original uploaded file.
    # --------------------------------------------------------

    sha256_hash = sha256_hex(data)

    # --------------------------------------------------------
    # Create document metadata
    # --------------------------------------------------------

    doc = Document(
        filename=file.filename or "unnamed",
        mime_type=file.content_type,
        owner_id=current_user.id,
        organization_id=current_user.organization_id,
    )

    db.add(doc)
    db.flush()

    # --------------------------------------------------------
    # Generate storage key
    # --------------------------------------------------------

    storage_key = (
        f"{current_user.organization_id}/"
        f"{doc.id}/"
        f"v1"
    )

    # --------------------------------------------------------
    # Encrypt file
    # --------------------------------------------------------

    blob = encrypt_file(
        plaintext=data,
        master_key=get_master_key(),
        key_version="v1",
    )

    # AES-GCM returns ciphertext + authentication tag.
    # Store both in object storage.

    encrypted_data = blob.ciphertext + blob.tag

    # --------------------------------------------------------
    # Store encrypted object
    # --------------------------------------------------------

    try:
        storage.put(
            storage_key,
            encrypted_data,
            file.content_type or "application/octet-stream",
        )

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to store encrypted document: {str(exc)}",
        )

    # --------------------------------------------------------
    # Create document version
    #
    # nonce + SHA-256 hash belong to DocumentVersion.
    # --------------------------------------------------------

    version = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        storage_key=storage_key,
        nonce=blob.nonce,
        sha256_hash=sha256_hash,
    )

    db.add(version)
    db.flush()

    # --------------------------------------------------------
    # Store encryption metadata
    #
    # EncryptionKey stores:
    # - wrapped_key
    # - key_version
    #
    # nonce is stored on DocumentVersion.
    # --------------------------------------------------------

    encryption_key = EncryptionKey(
        document_version_id=version.id,
        wrapped_key=blob.wrapped_key,
        key_version=blob.key_version,
    )

    db.add(encryption_key)

    # --------------------------------------------------------
    # Commit metadata
    # --------------------------------------------------------

    try:
        db.commit()
        db.refresh(doc)

    except Exception:
        db.rollback()

        # Remove encrypted object if database commit fails
        try:
            storage.delete(storage_key)
        except Exception:
            pass

        raise

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "mime_type": doc.mime_type,
        "size": len(data),
        "sha256_hash": sha256_hash,
        "storage_key": storage_key,
        "version": 1,
        "encrypted": True,
        "key_version": blob.key_version,
    }


# ============================================================
# List documents
# ============================================================

@router.get(
    "",
    dependencies=[
        Depends(
            require_permission("document:read")
        )
    ],
)
def list_documents(
    page: int = 1,
    size: int = 20,
    filename: str | None = None,
    sort: str = "-created_at",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="page must be greater than or equal to 1",
        )

    if size < 1 or size > 100:
        raise HTTPException(
            status_code=400,
            detail="size must be between 1 and 100",
        )

    query = (
        db.query(Document)
        .filter(
            Document.organization_id
            == current_user.organization_id,
            Document.is_archived.is_(False),
        )
    )

    if filename:
        query = query.filter(
            Document.filename.ilike(
                f"%{filename}%"
            )
        )

    if sort == "-created_at":
        query = query.order_by(
            Document.created_at.desc()
        )

    elif sort == "created_at":
        query = query.order_by(
            Document.created_at.asc()
        )

    else:
        raise HTTPException(
            status_code=400,
            detail=(
                "sort must be "
                "'created_at' or '-created_at'"
            ),
        )

    documents = (
        query
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return documents


# ============================================================
# Get document metadata
# ============================================================

@router.get(
    "/{doc_id}",
    dependencies=[
        Depends(
            require_permission("document:read")
        )
    ],
)
def get_document(
    doc_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    doc = _get_owned_or_404(
        db,
        doc_id,
        current_user,
    )

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "mime_type": doc.mime_type,
        "owner_id": str(doc.owner_id),
        "organization_id": str(
            doc.organization_id
        ),
        "is_archived": doc.is_archived,
        "created_at": doc.created_at,
    }


# ============================================================
# Download document
# ============================================================

@router.get(
    "/{doc_id}/download",
    dependencies=[
        Depends(
            require_permission("document:read")
        )
    ],
)
def download_document(
    doc_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # --------------------------------------------------------
    # Find document
    # --------------------------------------------------------

    doc = _get_owned_or_404(
        db,
        doc_id,
        current_user,
    )

    # --------------------------------------------------------
    # Get latest version
    # --------------------------------------------------------

    version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.document_id == doc.id
        )
        .order_by(
            DocumentVersion.version_number.desc()
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Document version not found",
        )

    # --------------------------------------------------------
    # Get encryption metadata
    # --------------------------------------------------------

    encryption_key = (
        db.query(EncryptionKey)
        .filter(
            EncryptionKey.document_version_id
            == version.id
        )
        .first()
    )

    if not encryption_key:
        raise HTTPException(
            status_code=404,
            detail="Encryption metadata not found",
        )

    # --------------------------------------------------------
    # Read encrypted object
    # --------------------------------------------------------

    try:
        encrypted_data = storage.get(
            version.storage_key
        )

    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Document file not found in storage",
        )

    # --------------------------------------------------------
    # Validate encrypted data
    #
    # AES-GCM authentication tag is 16 bytes.
    # --------------------------------------------------------

    if len(encrypted_data) < 16:
        raise HTTPException(
            status_code=500,
            detail="Stored encrypted document is invalid",
        )

    # --------------------------------------------------------
    # Separate ciphertext and authentication tag
    # --------------------------------------------------------

    ciphertext = encrypted_data[:-16]
    tag = encrypted_data[-16:]

    # --------------------------------------------------------
    # Reconstruct encrypted blob
    #
    # nonce comes from DocumentVersion.
    # wrapped_key comes from EncryptionKey.
    # --------------------------------------------------------

    blob = EncryptedBlob(
        ciphertext=ciphertext,
        nonce=version.nonce,
        tag=tag,
        wrapped_key=encryption_key.wrapped_key,
        key_version=encryption_key.key_version,
    )

    # --------------------------------------------------------
    # Decrypt
    # --------------------------------------------------------

    try:
        plaintext = decrypt_file(
            blob,
            get_master_key(),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to decrypt document",
        )

    # --------------------------------------------------------
    # Verify SHA-256 integrity
    #
    # Recompute the hash from the decrypted original
    # file and compare it with the stored hash.
    # --------------------------------------------------------

    if version.sha256_hash:
        calculated_hash = sha256_hex(plaintext)

        if calculated_hash != version.sha256_hash:
            raise HTTPException(
                status_code=500,
                detail="Document integrity verification failed",
            )

    # --------------------------------------------------------
    # Return original file
    # --------------------------------------------------------

    return StreamingResponse(
        io.BytesIO(plaintext),
        media_type=(
            doc.mime_type
            or "application/octet-stream"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; filename="{doc.filename}"'
            )
        },
    )


# ============================================================
# Rename document
# ============================================================

@router.patch(
    "/{doc_id}",
    dependencies=[
        Depends(
            require_permission("document:update")
        )
    ],
)
def update_document(
    doc_id: UUID,
    payload: DocumentUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    doc = _get_owned_or_404(
        db,
        doc_id,
        current_user,
    )

    if payload.filename:
        doc.filename = payload.filename

    db.commit()
    db.refresh(doc)

    return {
        "id": str(doc.id),
        "filename": doc.filename,
    }


# ============================================================
# Archive document
# ============================================================

@router.delete(
    "/{doc_id}",
    dependencies=[
        Depends(
            require_permission("document:delete")
        )
    ],
)
def archive_document(
    doc_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    doc = _get_owned_or_404(
        db,
        doc_id,
        current_user,
    )

    doc.is_archived = True

    db.commit()

    return {
        "status": "archived",
        "id": str(doc.id),
    }