from datetime import timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from fastapi.security import (
    OAuth2PasswordRequestForm
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.user import (
    UserCreate,
    UserResponse,
    Token
)

from app.services.user_service import (
    register_user,
    authenticate_user
)

from app.security.auth import (
    create_access_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# =========================================================
# REGISTER
# =========================================================

@router.post(
    "/register",
    response_model=UserResponse
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    result = register_user(
        db=db,
        username=user.username,
        email=user.email,
        password=user.password
    )


    if result == "USERNAME_EXISTS":

        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )


    if result == "EMAIL_EXISTS":

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )


    return result


# =========================================================
# LOGIN
# =========================================================

@router.post(
    "/login",
    response_model=Token
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = authenticate_user(
        db=db,
        username=form_data.username,
        password=form_data.password
    )


    if user is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )


    if not user.is_active:

        raise HTTPException(
            status_code=400,
            detail="User account is inactive"
        )


    access_token_expires = timedelta(
        minutes=30
    )


    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role
        },
        expires_delta=access_token_expires
    )


    return {
        "access_token": access_token,
        "token_type": "bearer"
    }