from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.api.auth import get_current_user


def require_permission(code: str):
    def checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        perms = {
            p.code
            for role in current_user.roles
            for p in role.permissions
        }

        if code not in perms:
            raise HTTPException(
                status_code=403,
                detail=f"Missing permission: {code}",
            )

        return current_user

    return checker