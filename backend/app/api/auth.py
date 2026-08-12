from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import jwt

from app.core.config import settings
from app.core.redis import redis_client
from app.db.session import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password
from app.core.tokens import (
    create_access_token,
    create_refresh_token,
)


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    organization_id: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


def get_current_user(
    token: str,
    db: Session = Depends(get_db),
):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
        )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid access token",
            )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid access token",
            )

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    user = db.query(User).filter_by(id=user_id).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user


@router.post("/register")
def register(
    payload: RegisterIn,
    db: Session = Depends(get_db),
):
    if db.query(User).filter_by(email=payload.email).first():
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        organization_id=payload.organization_id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": str(user.id)
    }


@router.post("/login")
def login(
    payload: LoginIn,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter_by(email=payload.email)
        .first()
    )

    if not user or not verify_password(
        payload.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
    }


@router.post("/logout")
def logout(token_id: str):
    redis_client.delete(f"refresh:{token_id}")

    return {
        "status": "revoked"
    }


@router.get("/me")
def me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
    }