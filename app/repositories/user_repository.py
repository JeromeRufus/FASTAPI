from sqlalchemy.orm import Session

from app.models.user import User


# =========================================================
# GET USER BY USERNAME
# =========================================================

def get_user_by_username(
    db: Session,
    username: str
):

    return (
        db.query(User)
        .filter(
            User.username == username
        )
        .first()
    )


# =========================================================
# GET USER BY EMAIL
# =========================================================

def get_user_by_email(
    db: Session,
    email: str
):

    return (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )


# =========================================================
# CREATE USER
# =========================================================

def create_user(
    db: Session,
    username: str,
    email: str,
    hashed_password: str
):

    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role="USER",
        is_active=True
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return user