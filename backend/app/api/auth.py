from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.db.session import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password
from app.core.tokens import create_access_token, create_refresh_token


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    organization_id: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


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

    return {"id": str(user.id)}


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