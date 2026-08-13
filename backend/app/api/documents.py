from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User


router = APIRouter(prefix="/documents", tags=["documents"])


@router.delete(
    "/{document_id}",
    dependencies=[Depends(require_permission("document:delete"))],
)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    db.delete(document)
    db.commit()

    return {"status": "deleted"}