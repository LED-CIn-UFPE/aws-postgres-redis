"""
Post Service - Gerenciamento de posts com cache Redis
"""
import json
import time
from typing import List, Optional
from psycopg2.extras import RealDictCursor
import redis

from src.models import Post, PostCreate, PostUpdate, PostWithAuthor, PostWithStats
from src.utils.cache import (
    CACHE_POST_PREFIX, CACHE_POST_LIST, CACHE_POST_PUBLISHED,
    CACHE_POST_VIEWS, CACHE_TTL
)


class PostService:
    """
    Serviço para gerenciar posts com cache em camadas

    Estratégia:
    - Sorted Sets: mantém IDs ordenados por timestamp
    - Write-through: ao criar post, adiciona ao Sorted Set (ZADD)
    - Cache-aside: busca do cache ou PostgreSQL
    - Contadores separados para views
    """

    @staticmethod
    def _cache_post(redis_client: redis.Redis, post_data: dict, post_id: int):
        """Cacheia dados completos do post (com autor)"""
        cache_key = f"{CACHE_POST_PREFIX}{post_id}"
        redis_client.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(post_data, default=str)
        )

    @staticmethod
    def _invalidate_list_cache(redis_client: redis.Redis):
        """Invalida caches de sorted sets"""
        redis_client.delete(CACHE_POST_LIST, CACHE_POST_PUBLISHED)

    @staticmethod
    def create_post(conn, redis_client: redis.Redis, data: PostCreate) -> Post:
        """
        Cria post com Write-Through Pattern

        DEMONSTRAÇÃO:
        1. INSERT no PostgreSQL
        2. Adiciona ID ao Sorted Set com ZADD (mantém ordem cronológica)
        3. Cacheia dados do post

        Vantagem: Novo post aparece imediatamente sem reconstruir lista!
        """
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO posts (title, slug, content, summary, author_id, published)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, title, slug, content, summary, author_id, published,
                          created_at, updated_at
                """,
                (data.title, data.slug, data.content, data.summary,
                 data.author_id, data.published)
            )
            result = cur.fetchone()
            conn.commit()

            post = Post(**result)
            timestamp = time.time()

            # Write-through: adiciona ao Sorted Set
            # Score = timestamp para ordenação cronológica
            redis_client.zadd(CACHE_POST_LIST, {post.id: timestamp})

            # Se publicado, adiciona também ao set de publicados
            if post.published:
                redis_client.zadd(CACHE_POST_PUBLISHED, {post.id: timestamp})

            # Define TTL nos sorted sets
            redis_client.expire(CACHE_POST_LIST, CACHE_TTL)
            redis_client.expire(CACHE_POST_PUBLISHED, CACHE_TTL)

            return post

    @staticmethod
    def get_post_by_id(conn, redis_client: redis.Redis, post_id: int,
                       increment_view: bool = False) -> Optional[PostWithStats]:
        """
        Busca post por ID com cache-aside

        DEMONSTRAÇÃO:
        - Cache hit: retorna em ~1ms
        - Cache miss: busca PostgreSQL + cacheia
        - Contador de views separado (INCR)
        """
        cache_key = f"{CACHE_POST_PREFIX}{post_id}"

        # Tenta buscar do cache
        cached = redis_client.get(cache_key)
        if cached:
            post_data = json.loads(cached)
            post = PostWithStats(**post_data)
        else:
            # Cache miss - busca do PostgreSQL com JOIN
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT p.*, a.name as author_name, a.email as author_email
                    FROM posts p
                    JOIN authors a ON p.author_id = a.id
                    WHERE p.id = %s
                    """,
                    (post_id,)
                )
                result = cur.fetchone()

                if not result:
                    return None

                # Converte para dict e adiciona views_count
                post_dict = dict(result)
                post_dict['views_count'] = 0
                post = PostWithStats(**post_dict)

                # Armazena no cache
                redis_client.setex(
                    cache_key,
                    CACHE_TTL,
                    json.dumps(post.model_dump(), default=str)
                )

        # Incrementa visualizações no Redis (contador em tempo real)
        if increment_view:
            views_key = f"{CACHE_POST_VIEWS}{post_id}"
            views_count = redis_client.incr(views_key)
            post.views_count = views_count
        else:
            # Busca contador atual se existir
            views_key = f"{CACHE_POST_VIEWS}{post_id}"
            views = redis_client.get(views_key)
            post.views_count = int(views) if views else 0

        return post

    @staticmethod
    def get_post_by_slug(conn, redis_client: redis.Redis, slug: str,
                         increment_view: bool = False) -> Optional[PostWithStats]:
        """Busca post por slug"""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM posts WHERE slug = %s", (slug,))
            result = cur.fetchone()

            if not result:
                return None

            return PostService.get_post_by_id(
                conn, redis_client, result['id'], increment_view
            )

    @staticmethod
    def list_posts(conn, redis_client: redis.Redis,
                   published_only: bool = False) -> List[PostWithAuthor]:
        """
        Lista posts com cache
        """
        cache_key = CACHE_POST_PUBLISHED if published_only else CACHE_POST_LIST

        # Tenta buscar do cache
        cached = redis_client.get(cache_key)
        if cached:
            posts_data = json.loads(cached)
            return [PostWithAuthor(**post) for post in posts_data]

        # Cache miss - busca do PostgreSQL
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT p.*, a.name as author_name, a.email as author_email
                FROM posts p
                JOIN authors a ON p.author_id = a.id
            """
            if published_only:
                query += " WHERE p.published = TRUE"
            query += " ORDER BY p.created_at DESC"

            cur.execute(query)
            results = cur.fetchall()
            posts = [PostWithAuthor(**dict(row)) for row in results]

            # Armazena no cache
            posts_json = json.dumps(
                [post.model_dump() for post in posts],
                default=str
            )
            
            redis_client.setex(cache_key, CACHE_TTL, posts_json)

            return posts

    @staticmethod
    def update_post(conn, redis_client: redis.Redis, post_id: int,
                    data: PostUpdate) -> Optional[Post]:
        """
        Atualiza post e invalida cache

        Se mudar status published, atualiza Sorted Sets
        """
        # Monta query dinâmica apenas com campos fornecidos
        update_fields = []
        values = []

        if data.title is not None:
            update_fields.append("title = %s")
            values.append(data.title)
        if data.content is not None:
            update_fields.append("content = %s")
            values.append(data.content)
        if data.summary is not None:
            update_fields.append("summary = %s")
            values.append(data.summary)
        if data.published is not None:
            update_fields.append("published = %s")
            values.append(data.published)

        if not update_fields:
            # Nenhuma alteração
            cached = redis_client.get(f"{CACHE_POST_PREFIX}{post_id}")
            if cached:
                post_data = json.loads(cached)
                return Post(**{k: v for k, v in post_data.items() if k in Post.model_fields})
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
                result = cur.fetchone()
                return Post(**result) if result else None

        values.append(post_id)

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = f"""
                UPDATE posts
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, title, slug, content, summary, author_id,
                          published, created_at, updated_at
            """
            cur.execute(query, values)
            result = cur.fetchone()
            conn.commit()

            if result:
                post = Post(**result)

                # Invalida cache do post
                cache_key = f"{CACHE_POST_PREFIX}{post_id}"
                redis_client.delete(cache_key)

                # Se mudou status de publicação, atualiza Sorted Sets
                if data.published is not None:
                    timestamp = time.time()

                    if data.published:
                        # Adiciona ao set de publicados
                        redis_client.zadd(CACHE_POST_PUBLISHED, {post_id: timestamp})
                    else:
                        # Remove do set de publicados
                        redis_client.zrem(CACHE_POST_PUBLISHED, post_id)

                # Invalida cache de listas
                PostService._invalidate_list_cache(redis_client)

                return post

            return None

    @staticmethod
    def delete_post(conn, redis_client: redis.Redis, post_id: int) -> bool:
        """
        Deleta post e remove de todos os caches

        DEMONSTRAÇÃO: Remove do Sorted Set com ZREM
        """
        with conn.cursor() as cur:
            cur.execute("DELETE FROM posts WHERE id = %s", (post_id,))
            deleted = cur.rowcount > 0
            conn.commit()

            if deleted:
                # Remove de todos os caches
                cache_key = f"{CACHE_POST_PREFIX}{post_id}"
                views_key = f"{CACHE_POST_VIEWS}{post_id}"
                redis_client.delete(cache_key, views_key)

                # Remove dos Sorted Sets com ZREM
                redis_client.zrem(CACHE_POST_LIST, post_id)
                redis_client.zrem(CACHE_POST_PUBLISHED, post_id)

            return deleted
