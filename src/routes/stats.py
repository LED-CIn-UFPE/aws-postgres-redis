"""
Rotas para estatísticas e métricas
Demonstra uso do Redis para dados em tempo real
"""
from fastapi import APIRouter, Depends, Query
from typing import List
from src.models import TopPost, MessageResponse
from src.services import StatsService
from src.core import get_db_connection, get_redis_client
import redis

router = APIRouter(prefix="/stats", tags=["Statistics"])

@router.get("/top-posts", response_model=List[TopPost])
def get_top_posts(
    limit: int = Query(10, ge=1, le=50, description="Número de posts no ranking"),
    conn=Depends(get_db_connection),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Retorna ranking dos posts mais visualizados

    DEMONSTRAÇÃO:
    - Combina dados do Redis (contadores) com PostgreSQL (metadados)
    - Contadores em tempo real no Redis
    - Cache do ranking por 1 minuto (dados quase em tempo real)
    - Perfeito para dashboards e métricas ao vivo!
    """
    return StatsService.get_top_posts(conn, redis_client, limit)


@router.get("/post/{post_id}/views")
def get_post_views(
    post_id: int,
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Retorna número de visualizações de um post

    DEMONSTRAÇÃO: Leitura direta do contador no Redis (instantâneo!)
    """
    views = StatsService.get_post_stats(redis_client, post_id)
    return {"post_id": post_id, "views_count": views}


@router.post("/persist-views", response_model=MessageResponse)
def persist_views(
    conn=Depends(get_db_connection),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Persiste contadores do Redis para PostgreSQL

    DEMONSTRAÇÃO:
    - Padrão de persistência assíncrona
    - Contadores ficam no Redis (rápido) e são persistidos periodicamente
    - Na prática, seria executado por cronjob
    - Permite análise histórica no PostgreSQL mantendo performance
    """
    count = StatsService.persist_views_to_db(conn, redis_client)
    return MessageResponse(
        message=f"{count} registros de visualizações persistidos no PostgreSQL"
    )
