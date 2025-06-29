"""Database initialization and setup"""
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)

from sqlalchemy import text
import logging

from core.config import DatabaseConfig
from models import BaseModel

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Database initialization and management"""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig.from_env()
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    @property
    def engine(self) -> AsyncEngine:
        """Get or create database engine"""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create session factory"""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return self._session_factory

    def _create_engine(self) -> AsyncEngine:
        """Create SQLAlchemy async engine"""
        database_url = self.config.get_database_url()

        config = {
            "pool_recycle": self.config.pool_recycle,
            "echo": self.config.echo,
            "echo_pool": self.config.echo_pool
        }
        if not self.config.test_mode:
            config.update({
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout
            })
        engine = create_async_engine(
            database_url,
            **config
        )

        logger.info(f"Created database engine for {database_url}")
        return engine

    async def create_tables(self) -> None:
        """Create all database tables"""
        async with self.engine.begin() as conn:
            # Import all models to ensure they're registered
            await conn.run_sync(BaseModel.metadata.create_all)
            logger.info("Database tables created successfully")

    async def drop_tables(self) -> None:
        """Drop all database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.drop_all)
            logger.info("Database tables dropped successfully")

    async def check_connection(self) -> bool:
        """Check database connection"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session (async context manager)"""
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def initialize(self, create_tables: bool = True) -> None:
        """Initialize database"""
        logger.info("Initializing database...")

        # Check connection
        if not await self.check_connection():
            raise RuntimeError("Failed to connect to database")

        # Create tables if requested
        if create_tables:
            await self.create_tables()

        logger.info("Database initialization completed")

    async def close(self) -> None:
        """Close database connections"""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connections closed")


# Global database instance
db_instance = DatabaseInitializer()
