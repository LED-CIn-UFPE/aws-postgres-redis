"""
Constantes e utilitários para cache Redis
"""

# ============= CACHE KEYS =============
CACHE_POST_PREFIX = "post:"  # String JSON: post:{id} → dados do post
CACHE_AUTHOR_PREFIX = "author:"  # String JSON: author:{id} → dados do autor
CACHE_POST_LIST = "posts:all:ids"  # Sorted Set: IDs ordenados por timestamp
CACHE_POST_PUBLISHED = "posts:published:ids"  # Sorted Set: IDs de publicados
CACHE_POST_VIEWS = "post:views:"  # String: contador de views
CACHE_TOP_POSTS = "posts:top"  # Cache temporário do ranking

# ============= TTLs =============
CACHE_TTL = 300  # 5 minutos - dados gerais
CACHE_AUTHOR_TTL = 600  # 10 minutos (autores mudam menos)
CACHE_TOP_POSTS_TTL = 60  # 1 minuto (dados quase em tempo real)
