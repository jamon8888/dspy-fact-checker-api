"""
Database configuration and connection utilities for the DSPy-Enhanced Fact-Checker API Platform.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import MetaData, text, create_engine
from sqlalchemy.orm import sessionmaker, Session
import logging
from typing import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Create a custom MetaData instance with naming convention
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

# Create the declarative base
Base = declarative_base(metadata=metadata)

# Global variables for database engine and session factory
engine = None
async_session_factory = None
sync_engine = None
sync_session_factory = None


def get_database_url(settings=None) -> str:
    """Get the async database URL from settings."""
    if settings is None:
        settings = get_settings()

    # For development, we'll use SQLite with async support
    # In production, this would be PostgreSQL
    if settings.ENVIRONMENT == "development":
        return "sqlite+aiosqlite:///./fact_checker.db"
    else:
        # PostgreSQL URL for production
        return (
            f"postgresql+asyncpg://{settings.DATABASE_USER}:"
            f"{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:"
            f"{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
        )


def get_sync_database_url(settings=None) -> str:
    """Get the sync database URL from settings."""
    if settings is None:
        settings = get_settings()

    # For development, we'll use SQLite with sync support
    # In production, this would be PostgreSQL
    if settings.ENVIRONMENT == "development":
        return "sqlite:///./fact_checker.db"
    else:
        # PostgreSQL URL for production
        return (
            f"postgresql+psycopg2://{settings.DATABASE_USER}:"
            f"{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:"
            f"{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
        )


async def init_database():
    """Initialize the database engine and session factory."""
    global engine, async_session_factory, sync_engine, sync_session_factory

    settings = get_settings()
    database_url = get_database_url(settings)
    sync_database_url = get_sync_database_url(settings)

    logger.info(f"Initializing database connection to: {database_url.split('@')[-1] if '@' in database_url else database_url}")

    # Create async engine
    engine = create_async_engine(
        database_url,
        echo=settings.DATABASE_ECHO,
        poolclass=NullPool if "sqlite" in database_url else None,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections every hour
        connect_args={
            "check_same_thread": False
        } if "sqlite" in database_url else {}
    )

    # Create sync engine for auth operations
    sync_engine = create_engine(
        sync_database_url,
        echo=settings.DATABASE_ECHO,
        poolclass=NullPool if "sqlite" in sync_database_url else None,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections every hour
        connect_args={
            "check_same_thread": False
        } if "sqlite" in sync_database_url else {}
    )

    # Create session factories
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    sync_session_factory = sessionmaker(
        sync_engine,
        class_=Session,
        expire_on_commit=False
    )

    logger.info("Database engines and session factories initialized successfully")


async def create_tables():
    """Create all database tables."""
    global engine
    
    if engine is None:
        await init_database()
    
    logger.info("Creating database tables...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created successfully")


async def drop_tables():
    """Drop all database tables (use with caution!)."""
    global engine
    
    if engine is None:
        await init_database()
    
    logger.warning("Dropping all database tables...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.warning("All database tables dropped")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    global async_session_factory
    
    if async_session_factory is None:
        await init_database()
    
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions."""
    async for session in get_async_session():
        yield session


async def close_database():
    """Close the database engine."""
    global engine
    
    if engine:
        logger.info("Closing database engine...")
        await engine.dispose()
        engine = None
        logger.info("Database engine closed")


class DatabaseHealthCheck:
    """Database health check utilities."""
    
    @staticmethod
    async def check_connection() -> bool:
        """Check if database connection is healthy."""
        try:
            async with get_db_session() as session:
                # Simple query to test connection
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    @staticmethod
    async def get_connection_info() -> dict:
        """Get database connection information."""
        global engine
        
        if engine is None:
            return {"status": "not_initialized"}
        
        try:
            async with get_db_session() as session:
                # Get database version and basic info
                if "sqlite" in str(engine.url):
                    result = await session.execute(text("SELECT sqlite_version()"))
                    version = result.scalar()
                    return {
                        "status": "connected",
                        "database_type": "SQLite",
                        "version": version,
                        "url": str(engine.url).replace(str(engine.url).split('@')[0].split('://')[-1] + '@', '***@') if '@' in str(engine.url) else str(engine.url)
                    }
                else:
                    result = await session.execute(text("SELECT version()"))
                    version = result.scalar()
                    return {
                        "status": "connected",
                        "database_type": "PostgreSQL",
                        "version": version.split(' ')[0] if version else "unknown",
                        "url": str(engine.url).replace(str(engine.url).split('@')[0].split('://')[-1] + '@', '***@')
                    }
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Sync session generator
def get_sync_session() -> Generator[Session, None, None]:
    """Get a sync database session."""
    global sync_session_factory

    logger.info("get_sync_session() called")

    if sync_session_factory is None:
        logger.error("Sync database not initialized. Call init_database() first.")
        raise RuntimeError("Sync database not initialized. Call init_database() first.")

    logger.info("Creating sync database session")
    session = sync_session_factory()
    try:
        logger.info("Yielding sync database session")
        yield session
        logger.info("Sync database session completed successfully")
    except Exception as e:
        logger.error(f"Sync database session error: {e}")
        session.rollback()
        raise
    finally:
        logger.info("Closing sync database session")
        session.close()


# Dependencies for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database sessions."""
    async for session in get_async_session():
        yield session


def get_sync_db() -> Generator[Session, None, None]:
    """FastAPI dependency for sync database sessions."""
    logger.info("get_sync_db() called - creating sync database session")
    try:
        yield from get_sync_session()
        logger.info("get_sync_db() completed successfully")
    except Exception as e:
        logger.error(f"get_sync_db() failed: {e}")
        raise
