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
    }


# ============================================================
# List documents
# ============================================================

@router.get(
    "",
    dependencies=[
        Depends(require_permission("document:read"))
    ],
)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Document)
        .filter(
            Document.organization_id == current_user.organization_id,
            Document.is_archived.is_(False),
        )
        .all()
    )


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

    doc.is_archived = True

    db.commit()

    return {
        "status": "archived",
        "id": str(doc.id),
    }