from pydantic import BaseModel

class JudgeDecision(BaseModel):
    is_correct: bool

class TextoAnonimizado(BaseModel):
    texto_anonimizado: str

class CaseStatus(BaseModel):
    status: str
    actions: str
    info: str
    department: str 