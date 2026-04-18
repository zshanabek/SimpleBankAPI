import random

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.account import Account
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import UserRegister


def _generate_account_number(db: Session) -> str:
    while True:
        number = str(random.randint(1_000_000_000, 9_999_999_999))
        if not db.query(Account).filter(Account.account_number == number).first():
            return number


def register_user(data: UserRegister, db: Session) -> User:
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = User(email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    db.flush()  # get user.id without committing

    account = Account(account_number=_generate_account_number(db), user_id=user.id)
    db.add(account)
    db.commit()
    db.refresh(user)
    return user


def login_user(email: str, password: str, db: Session) -> TokenResponse:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return TokenResponse(access_token=create_access_token(user.email))
