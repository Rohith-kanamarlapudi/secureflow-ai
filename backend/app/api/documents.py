from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.deps import require_permission
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


# ============================================================
# Upload configuration
# ============================================================

ALLOWED_MIME_TYPES = {
    "text/plain",
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/json",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


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
        Depends(require_permission("document:create"))
    ],
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Allowed types: PDF, TXT, PNG, JPEG and JSON."
            ),
        )

    # Read file to validate size
    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum file size is 10 MB.",
        )

    # Reset file pointer
    await file.seek(0)

    # Create database record
    doc = Document(
        filename=file.filename,
        mime_type=file.content_type,
        owner_id=current_user.id,
        organization_id=current_user.organization_id,
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "mime_type": doc.mime_type,
        "owner_id": str(doc.owner_id),
        "organization_id": str(doc.organization_id),
        "created_at": doc.created_at,
    }


# ============================================================
# List documents
# Pagination + filtering + sorting
# ============================================================

@router.get(
    "",
    dependencies=[
        Depends(require_permission("document:read"))
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
            Document.filename.ilike(f"%{filename}%")
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
            detail="sort must be 'created_at' or '-created_at'",
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
        Depends(require_permission("document:read"))
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
        "organization_id": str(doc.organization_id),
        "is_archived": doc.is_archived,
        "created_at": doc.created_at,
    }


# ============================================================
# Download document
# ============================================================

@router.get(
    "/{doc_id}/download",
    dependencies=[
        Depends(require_permission("document:read"))
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

    return FileResponse(
        f"./storage/{doc.filename}",
        filename=doc.filename,
        media_type=doc.mime_type,
    )


# ============================================================
# Rename document
# ============================================================

@router.patch(
    "/{doc_id}",
    dependencies=[
        Depends(require_permission("document:update"))
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

    # Validate filename
    if payload.filename is not None:

        new_filename = payload.filename.strip()

        if not new_filename:
            raise HTTPException(
                status_code=400,
                detail="Filename cannot be empty.",
            )

        doc.filename = new_filename

    db.commit()
    db.refresh(doc)

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "mime_type": doc.mime_type,
        "created_at": doc.created_at,
    }


# ============================================================
# Archive document
# ============================================================

@router.delete(
    "/{doc_id}",
    dependencies=[
        Depends(require_permission("document:delete"))
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

    # Soft delete / archive
    doc.is_archived = True

    db.commit()
    db.refresh(doc)

    return {
        "status": "archived",
        "id": str(doc.id),
    }