"""
Rotas para gerenciamento de posts
Demonstra cache patterns com Redis
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from src.models import (
    Post, PostCreate, PostUpdate, PostWithAuthor, PostWithStats, MessageResponse
)
from src.services import PostService
from src.core import get_db_connection, get_redis_client
import redis

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post("/", response_model=Post, status_code=status.HTTP_201_CREATED)
def create_post(
    data: PostCreate,
    conn=Depends(get_db_connection),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Cria um novo post

    DEMONSTRAÇÃO: Write-through - invalida cache de listas ao criar
    """
    try:
        return PostService.create_post(conn, redis_client, data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar post: {str(e)}"
        )


@router.get("/", response_model=List[PostWithAuthor])
def list_posts(
    published_only: bool = Query(False, description="Filtrar apenas publicados"),
    conn=Depends(get_db_connection),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Lista posts

    DEMONSTRAÇÃO: Cache-aside pattern
    - 1ª requisição: busca do PostgreSQL e armazena no Redis (cache miss)
    - Próximas requisições: retorna do Redis (cache hit) - muito mais rápido!
    - Cache expira em 5 minutos (TTL)
    """
    return PostService.list_posts(conn, redis_client, published_only)


@router.get("/{post_id}", response_model=PostWithStats)
def get_post(
    post_id: int,
    increment_view: bool = Query(
        True,
        description="Incrementar contador de visualizações"
    ),
    conn=Depends(get_db_connection),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Busca post por ID

    DEMONSTRAÇÃO:
    - Cache-aside: dados do post vêm do cache quando disponível
    - Contador em tempo real: views incrementadas no Redis (muito rápido!)
    - Cada visualização incrementa o contador sem acessar PostgreSQL
    """
    post = PostService.get_post_by_id(conn, redis_client, post_id, increment_view)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post não encontrado"
        )
    return post


@router.get("/slug/{slug}", response_model=PostWithStats)
def get_post_by_slug(
    slug: str,
    increment_view: bool = Query(True, description="Incrementar visualizações"),
    conn=Depends(get_db_connection),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Busca post por slug"""
    post = PostService.get_post_by_slug(conn, redis_client, slug, increment_view)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post não encontrado"
        )
    return post


@router.patch("/{post_id}", response_model=Post)
def update_post(
    post_id: int,
    data: PostUpdate,
    conn=Depends(get_db_connection),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Atualiza um post

    DEMONSTRAÇÃO: Write-through - invalida cache ao atualizar
    """
    post = PostService.update_post(conn, redis_client, post_id, data)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post não encontrado"
        )
    return post


@router.delete("/{post_id}", response_model=MessageResponse)
def delete_post(
    post_id: int,
    conn=Depends(get_db_connection),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Deleta um post

    DEMONSTRAÇÃO: Invalidação de cache
    """
    deleted = PostService.delete_post(conn, redis_client, post_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post não encontrado"
        )
    return MessageResponse(message="Post deletado com sucesso")
