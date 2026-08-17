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
    Signature,
)

from app.models.user import User
from app.models.share import DocumentShare
from app.schemas.share import ShareIn

from app.models.user import User

from app.storage.local import LocalStorage

from app.crypto.base import EncryptedBlob
from app.crypto.aes_service import encrypt_file
from app.crypto.decrypt_service import decrypt_file
from app.crypto.master_key import get_master_key
from app.crypto.hashing import sha256_hex

from app.crypto.signing import (
    sign_hash,
    verify_signature,
    encode_signature,
    decode_signature,
    encode_public_key,
    decode_public_key,
    load_public_key,
)

from app.crypto.signer import get_private_key


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

MAX_SIZE = 50 * 1024 * 1024


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
# Helpers
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
            Document.organization_id
            == current_user.organization_id,
        )
        .first()
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return doc


def _get_latest_version(
    db: Session,
    doc_id: UUID,
) -> DocumentVersion:

    version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.document_id
            == doc_id,
        )
        .order_by(
            DocumentVersion.created_at.desc()
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Document version not found",
        )

    return version


def _get_encryption_key(
    db: Session,
    version_id: UUID,
) -> EncryptionKey:

    encryption_key = (
        db.query(EncryptionKey)
        .filter(
            EncryptionKey.document_version_id
            == version_id,
        )
        .first()
    )

    if not encryption_key:
        raise HTTPException(
            status_code=404,
            detail="Encryption metadata not found",
        )

    return encryption_key


def _build_encrypted_blob(
    encrypted_data: bytes,
    version: DocumentVersion,
    encryption_key: EncryptionKey,
) -> EncryptedBlob:

    if len(encrypted_data) < 16:
        raise HTTPException(
            status_code=500,
            detail="Stored encrypted document is invalid",
        )

    ciphertext = encrypted_data[:-16]

    tag = encrypted_data[-16:]

    return EncryptedBlob(
        ciphertext=ciphertext,
        nonce=version.nonce,
        tag=tag,
        wrapped_key=encryption_key.wrapped_key,
        key_version=encryption_key.key_version,
    )


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

    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type: "
                f"{file.content_type}"
            ),
        )

    data = await file.read()

    if len(data) > MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                "File too large. "
                "Maximum size is 50 MB."
            ),
        )

    if len(data) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # --------------------------------------------------------
    # SHA-256
    # --------------------------------------------------------

    sha256_hash = sha256_hex(
        data
    )

    # --------------------------------------------------------
    # Create document
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
    # Storage key
    # --------------------------------------------------------

    storage_key = (
        f"{current_user.organization_id}/"
        f"{doc.id}/"
        f"v1"
    )

    # --------------------------------------------------------
    # Encrypt
    # --------------------------------------------------------

    try:

        blob = encrypt_file(
            plaintext=data,
            master_key=get_master_key(),
            key_version="v1",
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Encryption failed: {exc}",
        )

    # --------------------------------------------------------
    # Store encrypted data
    # --------------------------------------------------------

    encrypted_data = (
        blob.ciphertext
        + blob.tag
    )

    try:

        storage.put(
            storage_key,
            encrypted_data,
            file.content_type
            or "application/octet-stream",
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to store encrypted "
                f"document: {exc}"
            ),
        )

    # --------------------------------------------------------
    # Create version
    # --------------------------------------------------------

    try:

        version = DocumentVersion(
            document_id=doc.id,
            version_number="1",
            storage_key=storage_key,
            nonce=blob.nonce,
            sha256_hash=sha256_hash,
        )

        db.add(version)

        db.flush()

        # ----------------------------------------------------
        # Encryption metadata
        # ----------------------------------------------------

        encryption_key = EncryptionKey(
            document_version_id=version.id,
            wrapped_key=blob.wrapped_key,
            key_version=blob.key_version,
        )

        db.add(encryption_key)

        db.commit()

        db.refresh(doc)

    except Exception as exc:

        db.rollback()

        try:
            storage.delete(
                storage_key
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save document "
                f"metadata: {exc}"
            ),
        )

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "mime_type": doc.mime_type,
        "size": len(data),
        "sha256_hash": sha256_hash,
        "storage_key": storage_key,
        "version": "1",
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
            detail=(
                "page must be greater than "
                "or equal to 1"
            ),
        )

    if size < 1 or size > 100:
        raise HTTPException(
            status_code=400,
            detail=(
                "size must be between 1 and 100"
            ),
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

    return (
        query
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )


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

    doc = _get_owned_or_404(
        db,
        doc_id,
        current_user,
    )

    version = _get_latest_version(
        db,
        doc.id,
    )

    encryption_key = _get_encryption_key(
        db,
        version.id,
    )

    try:

        encrypted_data = storage.get(
            version.storage_key
        )

    except Exception:

        raise HTTPException(
            status_code=404,
            detail=(
                "Document file not found "
                "in storage"
            ),
        )

    blob = _build_encrypted_blob(
        encrypted_data,
        version,
        encryption_key,
    )

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

    if version.sha256_hash:

        calculated_hash = sha256_hex(
            plaintext
        )

        if (
            calculated_hash
            != version.sha256_hash
        ):

            raise HTTPException(
                status_code=500,
                detail=(
                    "Document integrity "
                    "verification failed"
                ),
            )

    return StreamingResponse(
        io.BytesIO(plaintext),
        media_type=(
            doc.mime_type
            or "application/octet-stream"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; '
                f'filename="{doc.filename}"'
            )
        },
    )


# ============================================================
# Verify document integrity
# ============================================================

@router.get(
    "/{doc_id}/verify",
    dependencies=[
        Depends(
            require_permission("document:read")
        )
    ],
)
def verify_integrity(
    doc_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    doc = _get_owned_or_404(
        db,
        doc_id,
        current_user,
    )

    version = _get_latest_version(
        db,
        doc.id,
    )

    encryption_key = _get_encryption_key(
        db,
        version.id,
    )

    try:

        encrypted_data = storage.get(
            version.storage_key
        )

    except Exception:

        raise HTTPException(
            status_code=404,
            detail=(
                "Document file not found "
                "in storage"
            ),
        )

    blob = _build_encrypted_blob(
        encrypted_data,
        version,
        encryption_key,
    )

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

    computed_hash = sha256_hex(
        plaintext
    )

    if not version.sha256_hash:

        status = "NO_HASH"

    elif (
        computed_hash
        == version.sha256_hash
    ):

        status = "VALID"

    else:

        status = "TAMPERED"

    return {
        "status": status,
        "stored_hash": version.sha256_hash,
        "computed_hash": computed_hash,
        "document_id": str(doc.id),
        "version": version.version_number,
    }


# ============================================================
# Upload new document version
# ============================================================

@router.post(
    "/{doc_id}/versions",
    dependencies=[
        Depends(
            require_permission("document:update")
        )
    ],
)
async def upload_new_version(
    doc_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # --------------------------------------------------------
    # Verify document belongs to current user's organization
    # --------------------------------------------------------

    doc = _get_owned_or_404(
        db,
        doc_id,
        current_user,
    )

    # --------------------------------------------------------
    # Validate file
    # --------------------------------------------------------

    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type: "
                f"{file.content_type}"
            ),
        )

    data = await file.read()

    if len(data) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    if len(data) > MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                "File too large. "
                "Maximum size is 50 MB."
            ),
        )

    # --------------------------------------------------------
    # Determine next version number
    # --------------------------------------------------------

    latest = _get_latest_version(
        db,
        doc.id,
    )

    try:
        next_version_number = str(
            int(latest.version_number) + 1
        )
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=500,
            detail="Invalid existing version number",
        )

    # --------------------------------------------------------
    # SHA-256
    # --------------------------------------------------------

    sha256_hash = sha256_hex(data)

    # --------------------------------------------------------
    # Storage key
    # --------------------------------------------------------

    storage_key = (
        f"{current_user.organization_id}/"
        f"{doc.id}/"
        f"v{next_version_number}"
    )

    # --------------------------------------------------------
    # Encrypt
    # --------------------------------------------------------

    try:
        blob = encrypt_file(
            plaintext=data,
            master_key=get_master_key(),
            key_version="v1",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Encryption failed: {exc}",
        )

    # AES-GCM returns ciphertext and tag separately.
    # Store them together; nonce and wrapped key remain metadata.
    encrypted_data = (
        blob.ciphertext
        + blob.tag
    )

    # --------------------------------------------------------
    # Store encrypted bytes
    # --------------------------------------------------------

    try:
        storage.put(
            storage_key,
            encrypted_data,
            file.content_type
            or "application/octet-stream",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to store encrypted "
                f"document version: {exc}"
            ),
        )

    # --------------------------------------------------------
    # Save version + encryption metadata
    # --------------------------------------------------------

    try:
        version = DocumentVersion(
            document_id=doc.id,
            version_number=next_version_number,
            storage_key=storage_key,
            nonce=blob.nonce,
            sha256_hash=sha256_hash,
        )

        db.add(version)
        db.flush()

        encryption_key = EncryptionKey(
            document_version_id=version.id,
            wrapped_key=blob.wrapped_key,
            key_version=blob.key_version,
        )

        db.add(encryption_key)

        db.commit()
        db.refresh(version)

    except Exception as exc:
        db.rollback()

        # Prevent an orphaned storage object if DB metadata fails.
        try:
            storage.delete(storage_key)
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save version metadata: "
                f"{exc}"
            ),
        )

    return {
        "status": "created",
        "document_id": str(doc.id),
        "version_id": str(version.id),
        "version": next_version_number,
        "filename": doc.filename,
        "size": len(data),
        "sha256_hash": sha256_hash,
        "storage_key": storage_key,
        "encrypted": True,
        "key_version": blob.key_version,
    }


# ============================================================
# Version history
# ============================================================

@router.get(
    "/{doc_id}/versions",
    dependencies=[
        Depends(
            require_permission("document:read")
        )
    ],
)
def version_history(
    doc_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = _get_owned_or_404(
        db,
        doc_id,
        current_user,
    )

    versions = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.document_id == doc.id
        )
        .order_by(
            DocumentVersion.version_number.desc()
        )
        .all()
    )

    return [
        {
            "id": str(version.id),
            "document_id": str(version.document_id),
            "version": version.version_number,
            "storage_key": version.storage_key,
            "sha256_hash": version.sha256_hash,
            "created_at": version.created_at,
        }
        for version in versions
    ]


# ============================================================
# Download a specific document version
# ============================================================

@router.get(
    "/{doc_id}/versions/{version_id}/download",
    dependencies=[
        Depends(
            require_permission("document:read")
        )
    ],
)
def download_version(
    doc_id: UUID,
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # --------------------------------------------------------
    # Verify document belongs to current user's organization
    # --------------------------------------------------------

    doc = _get_owned_or_404(
        db,
        doc_id,
        current_user,
    )

    # --------------------------------------------------------
    # Get requested version
    # --------------------------------------------------------

    version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.id == version_id,
            DocumentVersion.document_id == doc.id,
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

    encryption_key = _get_encryption_key(
        db,
        version.id,
    )

    # --------------------------------------------------------
    # Get encrypted bytes
    # --------------------------------------------------------

    try:
        encrypted_data = storage.get(
            version.storage_key
        )
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=(
                "Document version file not found "
                "in storage"
            ),
        )

    # --------------------------------------------------------
    # Rebuild EncryptedBlob
    # --------------------------------------------------------

    blob = _build_encrypted_blob(
        encrypted_data,
        version,
        encryption_key,
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
            detail=(
                "Failed to decrypt document version"
            ),
        )

    # --------------------------------------------------------
    # Verify SHA-256 integrity
    # --------------------------------------------------------

    if version.sha256_hash:
        calculated_hash = sha256_hex(
            plaintext
        )

        if calculated_hash != version.sha256_hash:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Document version integrity "
                    "verification failed"
                ),
            )

    # --------------------------------------------------------
    # Return plaintext
    # --------------------------------------------------------

    return StreamingResponse(
        io.BytesIO(plaintext),
        media_type=(
            doc.mime_type
            or "application/octet-stream"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; '
                f'filename="{doc.filename}"'
            )
        },
    )


# ============================================================
# Sign document version
# ============================================================

@router.post(
    "/{doc_id}/versions/{version_id}/sign",
    dependencies=[
        Depends(
            require_permission("document:update")
        )
    ],
)
def sign_document_version(
    doc_id: UUID,
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    doc = _get_owned_or_404(
        db,
        doc_id,
        current_user,
    )

    version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.id == version_id,
            DocumentVersion.document_id
            == doc.id,
        )
        .first()
    )

    if not version:

        raise HTTPException(
            status_code=404,
            detail="Document version not found",
        )

    if not version.sha256_hash:

        raise HTTPException(
            status_code=400,
            detail=(
                "Document version has "
                "no SHA-256 hash"
            ),
        )

    existing_signature = (
        db.query(Signature)
        .filter(
            Signature.document_version_id
            == version.id,
        )
        .first()
    )

    if existing_signature:

        return {
            "status": "already_signed",
            "signature_id": str(
                existing_signature.id
            ),
            "document_id": str(doc.id),
            "version_id": str(version.id),
        }

    try:

        private_key = get_private_key()

        public_key = (
            private_key.public_key()
        )

        signature_bytes = sign_hash(
            private_key,
            version.sha256_hash,
        )

        public_key_pem = (
            public_key.public_bytes(
                encoding=__import__(
                    "cryptography.hazmat.primitives.serialization",
                    fromlist=["Encoding"],
                ).Encoding.PEM,
                format=__import__(
                    "cryptography.hazmat.primitives.serialization",
                    fromlist=["PublicFormat"],
                ).PublicFormat.SubjectPublicKeyInfo,
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Signing failed: {exc}",
        )

    signature = Signature(
        document_version_id=version.id,
        signer_id=current_user.id,
        signature=encode_signature(
            signature_bytes
        ),
        hash_at_signing=version.sha256_hash,
        public_key=encode_public_key(
            public_key_pem
        ),
        algorithm="RSA-PSS-SHA256",
    )

    try:

        db.add(signature)

        db.commit()

        db.refresh(signature)

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save signature: "
                f"{exc}"
            ),
        )

    return {
        "status": "signed",
        "signature_id": str(
            signature.id
        ),
        "document_id": str(doc.id),
        "version_id": str(version.id),
        "signer_id": str(
            current_user.id
        ),
        "algorithm": signature.algorithm,
        "hash_at_signing": (
            signature.hash_at_signing
        ),
        "created_at": signature.created_at,
    }


# ============================================================
# Verify digital signature
# ============================================================

@router.get(
    "/{doc_id}/versions/{version_id}/signature",
    dependencies=[
        Depends(
            require_permission("document:read")
        )
    ],
)
def verify_signature_status(
    doc_id: UUID,
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    doc = _get_owned_or_404(
        db,
        doc_id,
        current_user,
    )

    version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.id == version_id,
            DocumentVersion.document_id
            == doc.id,
        )
        .first()
    )

    if not version:

        raise HTTPException(
            status_code=404,
            detail="Document version not found",
        )

    signature = (
        db.query(Signature)
        .filter(
            Signature.document_version_id
            == version.id,
        )
        .first()
    )

    if not signature:

        raise HTTPException(
            status_code=404,
            detail="Signature not found",
        )

    encryption_key = _get_encryption_key(
        db,
        version.id,
    )

    try:

        encrypted_data = storage.get(
            version.storage_key
        )

    except Exception:

        raise HTTPException(
            status_code=404,
            detail=(
                "Document file not found "
                "in storage"
            ),
        )

    blob = _build_encrypted_blob(
        encrypted_data,
        version,
        encryption_key,
    )

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

    computed_hash = sha256_hex(
        plaintext
    )

    modified = (
        computed_hash
        != signature.hash_at_signing
    )

    try:

        public_key = load_public_key(
            decode_public_key(
                signature.public_key
            )
        )

        signature_bytes = (
            decode_signature(
                signature.signature
            )
        )

        cryptographic_signature_valid = (
            verify_signature(
                public_key,
                signature_bytes,
                signature.hash_at_signing,
            )
        )

    except Exception:

        cryptographic_signature_valid = False

    valid = (
        cryptographic_signature_valid
        and not modified
    )

    status = (
        "VALID"
        if valid
        else "INVALID"
    )

    return {
        "status": status,
        "signer": str(
            signature.signer_id
        ),
        "signed_at": signature.created_at,
        "modified": modified,
        "signature_valid": (
            cryptographic_signature_valid
        ),
        "stored_hash": (
            signature.hash_at_signing
        ),
        "computed_hash": computed_hash,
        "document_id": str(doc.id),
        "version": version.version_number,
        "algorithm": signature.algorithm,
    }


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
# ============================================================
# Create document share
# ============================================================

@router.post(
    "/{doc_id}/shares",
    dependencies=[
        Depends(
            require_permission("document:share")
        )
    ],
)
def create_share(
    doc_id: UUID,
    payload: ShareIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # --------------------------------------------------------
    # Verify document belongs to current user's organization
    # --------------------------------------------------------

    doc = _get_owned_or_404(
        db,
        doc_id,
        current_user,
    )

    # --------------------------------------------------------
    # Verify target user exists
    # and belongs to the same organization
    # --------------------------------------------------------

    shared_with_user = (
        db.query(User)
        .filter(
            User.id == payload.user_id,
            User.organization_id
            == current_user.organization_id,
            User.is_active.is_(True),
        )
        .first()
    )

    if not shared_with_user:
        raise HTTPException(
            status_code=404,
            detail=(
                "User not found in the "
                "current organization"
            ),
        )

    # --------------------------------------------------------
    # Validate permission level
    # --------------------------------------------------------

    if payload.permission_level not in {
        "view",
        "edit",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "permission_level must be "
                "'view' or 'edit'"
            ),
        )

    # --------------------------------------------------------
    # Prevent sharing with yourself
    # --------------------------------------------------------

    if shared_with_user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot share a document with yourself",
        )

    # --------------------------------------------------------
    # Check for an existing active share
    # --------------------------------------------------------

    existing_share = (
        db.query(DocumentShare)
        .filter(
            DocumentShare.document_id
            == doc.id,
            DocumentShare.shared_with_user_id
            == shared_with_user.id,
            DocumentShare.revoked_at.is_(None),
        )
        .first()
    )

    if existing_share:

        # If an existing share has expired,
        # allow a new share to be created.
        if (
            existing_share.expires_at is not None
            and existing_share.expires_at
            <= __import__(
                "datetime"
            ).datetime.now(
                __import__(
                    "datetime"
                ).timezone.utc
            )
        ):
            existing_share.revoked_at = (
                __import__(
                    "datetime"
                ).datetime.now(
                    __import__(
                        "datetime"
                    ).timezone.utc
                )
            )

            db.flush()

        else:
            raise HTTPException(
                status_code=409,
                detail=(
                    "An active share already exists "
                    "for this user"
                ),
            )

    # --------------------------------------------------------
    # Validate expiry
    # --------------------------------------------------------

    if payload.expires_at is not None:

        from datetime import datetime, timezone

        expires_at = payload.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if expires_at <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail=(
                    "expires_at must be in the future"
                ),
            )

    # --------------------------------------------------------
    # Create share
    # --------------------------------------------------------

    share = DocumentShare(
        document_id=doc.id,
        shared_with_user_id=shared_with_user.id,
        permission_level=payload.permission_level,
        expires_at=payload.expires_at,
        revoked_at=None,
    )

    try:

        db.add(share)
        db.commit()
        db.refresh(share)

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to create document share: "
                f"{exc}"
            ),
        )

    return {
        "status": "created",
        "id": str(share.id),
        "document_id": str(share.document_id),
        "shared_with_user_id": str(
            share.shared_with_user_id
        ),
        "permission_level": (
            share.permission_level
        ),
        "expires_at": share.expires_at,
        "revoked_at": share.revoked_at,
    }