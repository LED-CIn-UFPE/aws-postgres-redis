"""
Schemas Pydantic para Post
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PostBase(BaseModel):
    """Schema base para Post"""
    title: str = Field(..., min_length=1, max_length=500)
    slug: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    summary: Optional[str] = None
    published: bool = False


class PostCreate(PostBase):
    """Schema para criação de Post"""
    author_id: int


class PostUpdate(BaseModel):
    """Schema para atualização de Post"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    summary: Optional[str] = None
    published: Optional[bool] = None


class Post(PostBase):
    """Schema completo de Post (com ID e timestamps)"""
    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostWithAuthor(Post):
    """Post com informações do autor incluídas"""
    author_name: str
    author_email: str


class PostWithStats(PostWithAuthor):
    """Post com estatísticas de visualizações"""
    views_count: int = 0


class PostStats(BaseModel):
    """Estatísticas de um post"""
    post_id: int
    views_count: int
    title: str


class TopPost(BaseModel):
    """Post no ranking de mais visualizados"""
    rank: int
    post_id: int
    title: str
    slug: str
    views_count: int
    author_name: str
