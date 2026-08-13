from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
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
# Delete document
# ============================================================

@router.delete(
    "/{document_id}",
    dependencies=[
        Depends(require_permission("document:delete"))
    ],
)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    db.delete(document)
    db.commit()

    return {
        "status": "deleted",
        "id": str(document_id),
    }