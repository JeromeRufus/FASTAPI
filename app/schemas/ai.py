from pydantic import BaseModel


class AIRequest(BaseModel):
    question: str


class AISource(BaseModel):
    type: str
    id: str


class AIResponse(BaseModel):
    question: str
    answer: str
    sources: list[AISource] = []
