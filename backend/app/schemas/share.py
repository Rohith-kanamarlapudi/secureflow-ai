from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ShareIn(BaseModel):
    user_id: UUID

    permission_level: str = Field(
        ...,
        pattern="^(view|edit)$",
    )

    expires_at: datetime | None = None


class ShareOut(BaseModel):
    id: UUID