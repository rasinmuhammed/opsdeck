"""
Authentication utilities for OpsDeck.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from opsdeck.auth.models import AdminUserMixin


async def create_superuser(
    session: AsyncSession,
    user_model: type[AdminUserMixin],
    username: str,
    email: str,
    password: str,
) -> AdminUserMixin:
    """
    Helper function to create a superuser.

    Usage:
        await create_superuser(session, User, "admin", "admin@example.com", "password")
        await session.commit()
    """
    from sqlalchemy import select

    # Check existing
    result = await session.execute(
        select(user_model).where(user_model.username == username)
    )
    if result.scalar_one_or_none():
        raise ValueError(f"User {username} already exists")

    # Hash password
    hashed = user_model.hash_password(password)

    # Create user
    user = user_model(
        username=username,
        email=email,
        password_hash=hashed,
        is_superuser=True,
        is_active=True,
        roles=["admin"],
    )

    session.add(user)
    return user
