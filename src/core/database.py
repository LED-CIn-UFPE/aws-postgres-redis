"""
Gerenciamento de conexões com PostgreSQL e Redis
"""
from psycopg2.pool import SimpleConnectionPool
import redis
from typing import Optional
from src.core.config import get_settings


class DatabaseManager:
    """Gerenciador de conexões com PostgreSQL"""

    def __init__(self):
        self.settings = get_settings()
        self.pool: Optional[SimpleConnectionPool] = None

    def init_pool(self):
        """Inicializa o pool de conexões"""
        if self.pool is None:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=self.settings.database_host,
                port=self.settings.database_port,
                database=self.settings.database_name,
                user=self.settings.database_user,
                password=self.settings.database_password
            )

    def get_connection(self):
        """Obtém uma conexão do pool"""
        if self.pool is None:
            self.init_pool()
        return self.pool.getconn()

    def return_connection(self, conn):
        """Retorna uma conexão ao pool"""
        if self.pool:
            self.pool.putconn(conn)

    def close_pool(self):
        """Fecha o pool de conexões"""
        if self.pool:
            self.pool.closeall()


class RedisManager:
    """Gerenciador de conexões com Redis"""

    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[redis.Redis] = None

    def get_client(self) -> redis.Redis:
        """Retorna cliente Redis"""
        if self.client is None:
            self.client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_db,
                decode_responses=True  # Retorna strings ao invés de bytes
            )
        return self.client

    def close(self):
        """Fecha conexão com Redis"""
        if self.client:
            self.client.close()


# Instâncias globais
db_manager = DatabaseManager()
redis_manager = RedisManager()


def get_db_connection():
    """Dependency injection para FastAPI - PostgreSQL"""
    conn = db_manager.get_connection()
    try:
        yield conn
    finally:
        db_manager.return_connection(conn)


def get_redis_client():
    """Dependency injection para FastAPI - Redis"""
    return redis_manager.get_client()
