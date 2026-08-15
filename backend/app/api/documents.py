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
from app.models.document import Document, DocumentVersion
from app.models.user import User
from app.storage.local import LocalStorage


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
    # Store file object
    # --------------------------------------------------------

    try:
        storage.put(
            storage_key,
            data,
            file.content_type,
        )

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to store document: {str(exc)}",
        )

    # --------------------------------------------------------
    # Create document version
    # --------------------------------------------------------

    version = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        storage_key=storage_key,
    )

    db.add(version)

    # --------------------------------------------------------
    # Commit metadata
    # --------------------------------------------------------

    try:
        db.commit()
        db.refresh(doc)

    except Exception:
        db.rollback()

        # Best-effort cleanup of orphaned object
        try:
            storage.delete(storage_key)
        except Exception:
            pass

        raise

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "mime_type": doc.mime_type,
        "size": len(data),
        "storage_key": storage_key,
        "version": 1,
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

    # --------------------------------------------------------
    # Validate page
    # --------------------------------------------------------

    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="page must be greater than or equal to 1",
        )

    # --------------------------------------------------------
    # Validate size
    # --------------------------------------------------------

    if size < 1 or size > 100:
        raise HTTPException(
            status_code=400,
            detail="size must be between 1 and 100",
        )

    # --------------------------------------------------------
    # Base query
    # --------------------------------------------------------

    query = (
        db.query(Document)
        .filter(
            Document.organization_id
            == current_user.organization_id,
            Document.is_archived.is_(False),
        )
    )

    # --------------------------------------------------------
    # Filename filtering
    # --------------------------------------------------------

    if filename:
        query = query.filter(
            Document.filename.ilike(
                f"%{filename}%"
            )
        )

    # --------------------------------------------------------
    # Sorting
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------

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
    # Read object from storage
    # --------------------------------------------------------

    try:
        data = storage.get(
            version.storage_key
        )

    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Document file not found in storage",
        )

    # --------------------------------------------------------
    # Stream file to client
    # --------------------------------------------------------

    return StreamingResponse(
        io.BytesIO(data),
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