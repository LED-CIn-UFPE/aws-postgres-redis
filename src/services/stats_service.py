"""
Stats Service - Estatísticas e rankings
"""
import json
from typing import List
from psycopg2.extras import RealDictCursor
import redis

from src.models import TopPost
from src.utils.cache import CACHE_POST_VIEWS, CACHE_TOP_POSTS, CACHE_TOP_POSTS_TTL


class StatsService:
    """Serviço para estatísticas e métricas em tempo real"""

    @staticmethod
    def get_post_stats(redis_client: redis.Redis, post_id: int) -> int:
        """
        Retorna número de visualizações de um post

        DEMONSTRAÇÃO: Leitura direta do contador Redis (instantâneo!)
        """
        views_key = f"{CACHE_POST_VIEWS}{post_id}"
        views = redis_client.get(views_key)
        return int(views) if views else 0

    @staticmethod
    def get_top_posts(conn, redis_client: redis.Redis, limit: int = 10) -> List[TopPost]:
        """
        Retorna ranking dos posts mais visualizados

        DEMONSTRAÇÃO:
        - Combina dados do Redis (contadores) com PostgreSQL (metadados)
        - Contadores em tempo real no Redis
        - Cache do ranking por 1 minuto (dados quase em tempo real)
        - Perfeito para dashboards e métricas ao vivo!

        Quando uma key de post views expira, assumimos
        """
        # Tenta buscar do cache
        cached = redis_client.get(CACHE_TOP_POSTS)
        if cached:
            return [TopPost(**post) for post in json.loads(cached)]

        # Busca todas as visualizações do Redis usando SCAN
        views_pattern = f"{CACHE_POST_VIEWS}*"
        post_views = {}

        for key in redis_client.scan_iter(match=views_pattern):
            post_id = int(key.split(":")[-1])
            views = int(redis_client.get(key) or 0)
            if views > 0:
                post_views[post_id] = views

        if not post_views:
            return []

        # Busca informações dos posts do PostgreSQL
        post_ids = list(post_views.keys())
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT p.id, p.title, p.slug, a.name as author_name
                FROM posts p
                JOIN authors a ON p.author_id = a.id
                WHERE p.id = ANY(%s) AND p.published = TRUE
                """,
                (post_ids,)
            )
            posts_info = {row['id']: row for row in cur.fetchall()}

        # Monta ranking ordenado por views (descendente)
        top_posts = []
        for rank, (post_id, views) in enumerate(
            sorted(post_views.items(), key=lambda x: x[1], reverse=True)[:limit],
            start=1
        ):
            if post_id in posts_info:
                info = posts_info[post_id]
                top_posts.append(TopPost(
                    rank=rank,
                    post_id=post_id,
                    title=info['title'],
                    slug=info['slug'],
                    views_count=views,
                    author_name=info['author_name']
                ))

        # Cacheia por 1 minuto (dados quase em tempo real)
        if top_posts:
            redis_client.setex(
                CACHE_TOP_POSTS,
                CACHE_TOP_POSTS_TTL,
                json.dumps([post.model_dump() for post in top_posts])
            )

        return top_posts

    # Em um cenário realista, deveriamos resetar o cache contendo um delta das views para evitar double count
    @staticmethod
    def persist_views_to_db(conn, redis_client: redis.Redis) -> int:
        """
        Persiste contadores de visualizações do Redis para PostgreSQL

        DEMONSTRAÇÃO:
        - Padrão de persistência assíncrona
        - Contadores ficam no Redis (rápido) e são persistidos periodicamente
        - Na prática, seria executado por cronjob/Lambda agendado
        - Permite análise histórica no PostgreSQL mantendo performance
        """
        views_pattern = f"{CACHE_POST_VIEWS}*"
        persisted_count = 0

        with conn.cursor() as cur:
            for key in redis_client.scan_iter(match=views_pattern):
                post_id = int(key.split(":")[-1])
                views = int(redis_client.get(key) or 0)

                if views > 0:
                    # Upsert na tabela post_views
                    cur.execute(
                        """
                        INSERT INTO post_views (post_id, views_count, date)
                        VALUES (%s, %s, CURRENT_DATE)
                        ON CONFLICT (post_id, date)
                        DO UPDATE SET views_count = post_views.views_count + EXCLUDED.views_count
                        """,
                        (post_id, views)
                    )
                    persisted_count += 1

            conn.commit()

        return persisted_count
