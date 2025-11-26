"""
Services - Lógica de negócio e acesso a dados
"""
from src.services.author_service import AuthorService
from src.services.post_service import PostService
from src.services.stats_service import StatsService

__all__ = [
    "AuthorService",
    "PostService",
    "StatsService",
]
