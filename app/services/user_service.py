from app.repositories.user_repository import (
    get_user_by_username,
    get_user_by_email,
    create_user
)

from app.security.auth import (
    hash_password,
    verify_password
)


# =========================================================
# REGISTER USER
# =========================================================

def register_user(
    db,
    username,
    email,
    password
):

    # Check username
    existing_username = (
        get_user_by_username(
            db=db,
            username=username
        )
    )

    if existing_username:

        return "USERNAME_EXISTS"


    # Check email
    existing_email = (
        get_user_by_email(
            db=db,
            email=email
        )
    )

    if existing_email:

        return "EMAIL_EXISTS"


    # Hash password
    hashed_password = hash_password(
        password
    )


    # Create user
    return create_user(
        db=db,
        username=username,
        email=email,
        hashed_password=hashed_password
    )


# =========================================================
# AUTHENTICATE USER
# =========================================================

def authenticate_user(
    db,
    username,
    password
):

    user = get_user_by_username(
        db=db,
        username=username
    )

    if user is None:

        return None


    if not verify_password(
        password,
        user.hashed_password
    ):

        return None


    return user