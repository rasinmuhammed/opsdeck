"""
Database session management for FastAPI Shadcn Admin.

Provides async session dependency injection.
"""

from __future__ import annotations

from typing import AsyncGenerator, TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


class DatabaseManager:
    """
    Database session manager for async SQLAlchemy.

    Usage:
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine("postgresql+asyncpg://...")
        db_manager = DatabaseManager(engine)

        # In FastAPI dependency
        async def get_session():
            async for session in db_manager.get_session():
                yield session
    """

    def __init__(self, engine: "AsyncEngine"):
        """
        Initialize database manager.

        Args:
            engine: SQLAlchemy async engine
        """
        self.engine = engine
        self.session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async database session for dependency injection.

        Yields:
            AsyncSession instance

        Example:
            @router.get("/users")
            async def list_users(session: AsyncSession = Depends(get_session)):
                users = await crud.list(session)
                return users
        """
        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_all_tables(self, base) -> None:
        """
        Create all database tables.

        Args:
            base: SQLAlchemy declarative base

        Example:
            from sqlalchemy.orm import declarative_base

            Base = declarative_base()
            await db_manager.create_all_tables(Base)
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(base.metadata.create_all)

    async def drop_all_tables(self, base) -> None:
        """
        Drop all database tables (use with caution!).

        Args:
            base: SQLAlchemy declarative base
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(base.metadata.drop_all)

    async def close(self) -> None:
        """Close database engine."""
        await self.engine.dispose()
