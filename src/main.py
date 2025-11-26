from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from src.core import get_settings, db_manager, redis_manager, get_redis_client
from src.models import HealthCheck
from src.routes import authors, posts, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia lifecycle do app"""
    # Startup
    db_manager.init_pool()
    redis_client = redis_manager.get_client()
    print("Aplicação inicializada")

    yield

    # Shutdown
    print("Fechando aplicação...")
    db_manager.close_pool()
    redis_manager.close()
    print("Conexões com bancos fechadas.")


# Inicializa FastAPI
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="",
    lifespan=lifespan,
    docs_url="/api/docs",  # Swagger UI em /api/docs
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authors.router, prefix="/api")
app.include_router(posts.router, prefix="/api")
app.include_router(stats.router, prefix="/api")


@app.get("/api/health", response_model=HealthCheck, tags=["Health"])
def health_check(redis_client=Depends(get_redis_client)):
    """
    Health check - verifica status de PostgreSQL e Redis
    """
    # Testa PostgreSQL
    postgres_ok = False
    try:
        conn = db_manager.get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            postgres_ok = True
        db_manager.return_connection(conn)
    except Exception:
        pass

    # Testa Redis
    redis_ok = False
    try:
        redis_ok = redis_client.ping()
    except Exception:
        pass

    status = "healthy" if (postgres_ok and redis_ok) else "unhealthy"

    return HealthCheck(
        status=status,
        postgres=postgres_ok,
        redis=redis_ok,
        version=settings.app_version
    )


# Serve frontend estático - DEVE SER O ÚLTIMO!
# O mount com html=True é um catch-all que serve index.html para qualquer rota não encontrada
# Por isso precisa vir depois de todos os endpoints da API
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
