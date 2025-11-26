"""
Schemas Pydantic comuns
"""
from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Resposta genérica com mensagem"""
    message: str


class HealthCheck(BaseModel):
    """Status de saúde da aplicação"""
    status: str
    postgres: bool
    redis: bool
    version: str
