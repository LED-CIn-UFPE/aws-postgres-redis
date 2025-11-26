"""
Author Service - Gerenciamento de autores com cache
"""
import json
from typing import List, Optional
from psycopg2.extras import RealDictCursor
import redis

from src.models import Author, AuthorCreate
from src.utils.cache import CACHE_AUTHOR_PREFIX, CACHE_AUTHOR_TTL


class AuthorService:
    """Serviço para gerenciar autores com cache em camada separada"""

    @staticmethod
    def _cache_author(redis_client: redis.Redis, author_data: dict, author_id: int):
        """Cacheia dados do autor"""
        cache_key = f"{CACHE_AUTHOR_PREFIX}{author_id}"
        redis_client.setex(
            cache_key,
            CACHE_AUTHOR_TTL,
            json.dumps(author_data, default=str)
        )

    @staticmethod
    def get_author_cached(redis_client: redis.Redis, conn, author_id: int) -> Optional[dict]:
        """
        Busca autor com cache-aside
        Retorna dict ao invés de Author para reutilização em composição

        DEMONSTRAÇÃO: Cache em Camadas
        - Autores cacheados separadamente dos posts
        - TTL maior (10min) pois autores mudam menos que posts
        - Se autor mudar nome, apenas invalida cache do autor
        """
        cache_key = f"{CACHE_AUTHOR_PREFIX}{author_id}"

        # Tenta cache primeiro
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

        # Cache miss - busca do PostgreSQL
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, name, email, bio, created_at FROM authors WHERE id = %s",
                (author_id,)
            )
            result = cur.fetchone()

            if not result:
                return None

            author_data = dict(result)

            # Armazena no cache
            AuthorService._cache_author(redis_client, author_data, author_id)
            return author_data

    @staticmethod
    def create_author(conn, data: AuthorCreate) -> Author:
        """Cria um novo autor"""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO authors (name, email, bio)
                VALUES (%s, %s, %s)
                RETURNING id, name, email, bio, created_at
                """,
                (data.name, data.email, data.bio)
            )
            result = cur.fetchone()
            conn.commit()
            return Author(**result)

    @staticmethod
    def get_author(conn, author_id: int) -> Optional[Author]:
        """Busca autor por ID (sem cache - para endpoint direto)"""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, name, email, bio, created_at FROM authors WHERE id = %s",
                (author_id,)
            )
            result = cur.fetchone()
            return Author(**result) if result else None

    @staticmethod
    def list_authors(conn) -> List[Author]:
        """Lista todos os autores"""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, name, email, bio, created_at FROM authors ORDER BY name"
            )
            results = cur.fetchall()
            return [Author(**row) for row in results]
