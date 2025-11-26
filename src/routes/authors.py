"""
Rotas para gerenciamento de autores
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from src.models import Author, AuthorCreate
from src.services import AuthorService
from src.core import get_db_connection

router = APIRouter(prefix="/authors", tags=["Authors"])

@router.post("/", response_model=Author, status_code=status.HTTP_201_CREATED)
def create_author(data: AuthorCreate, conn=Depends(get_db_connection)):
    """Cria um novo autor"""
    try:
        return AuthorService.create_author(conn, data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar autor: {str(e)}"
        )


@router.get("/{author_id}", response_model=Author)
def get_author(author_id: int, conn=Depends(get_db_connection)):
    """Busca autor por ID"""
    author = AuthorService.get_author(conn, author_id)
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autor não encontrado"
        )
    return author


@router.get("/", response_model=List[Author])
def list_authors(conn=Depends(get_db_connection)):
    """Lista todos os autores"""
    return AuthorService.list_authors(conn)
