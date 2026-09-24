from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import dummy_password_hash, hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


class EmailAlreadyRegisteredError(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == normalize_email(email)))


def register_user(db: Session, user_data: UserCreate) -> User:
    email = normalize_email(str(user_data.email))
    if get_user_by_email(db, email) is not None:
        raise EmailAlreadyRegisteredError

    user = User(
        name=user_data.name,
        email=email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmailAlreadyRegisteredError from exc

    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    stored_hash = user.password_hash if user is not None else dummy_password_hash
    password_is_valid = verify_password(password, stored_hash)
    if user is None or not password_is_valid:
        return None
    return user
