from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.ai import (
    AIRequest,
    AIResponse
)

from app.services.ai_service import ask_gemini_with_context

from app.security.auth import get_current_user


router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.post(
    "/ask",
    response_model=AIResponse
)
def ask_ai(
    request: AIRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    answer, sources = ask_gemini_with_context(
        db=db,
        question=request.question
    )

    return {
        "question": request.question,
        "answer": answer,
        "sources": sources
    }
