"""
Authentication service with session management.

Handles login, logout, and session verification.
"""

from __future__ import annotations

import os
from typing import Optional, TYPE_CHECKING

from fastapi import Request, Response, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from opsdeck.auth.models import AdminUser, SessionData
    from opsdeck.core.security import URLSigner


SESSION_COOKIE_NAME = "admin_session"
SESSION_COOKIE_MAX_AGE = 86400  # 24 hours in seconds
SESSION_COOKIE_MAX_AGE_REMEMBER = 2592000  # 30 days


class AuthService:
    """
    Authentication service for admin users.

    Handles login, logout, and session management using signed cookies.
    """

    def __init__(self, signer: "URLSigner", user_model: type["AdminUser"]):
        """
        Initialize auth service.

        Args:
            signer: URLSigner for cookie signing
            user_model: AdminUser model class
        """
        self.signer = signer
        self.user_model = user_model
        self.secure_cookies = (
            os.getenv("ADMIN_SECURE_COOKIES", "false").lower() == "true"
        )

    async def authenticate(
        self,
        session: "AsyncSession",
        username: str,
        password: str,
    ) -> Optional["AdminUser"]:
        """
        Authenticate a user by username and password.

        Args:
            session: Database session
            username: Username
            password: Plain text password

        Returns:
            AdminUser if authenticated, None otherwise
        """
        from sqlalchemy import select

        # Find user by username or email
        query = select(self.user_model).where(
            (self.user_model.username == username) | (self.user_model.email == username)
        )
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None

        if not user.is_active:
            return None

        if not user.verify_password(password):
            return None

        # Update last login
        user.update_last_login()
        await session.commit()

        return user

    def create_session_cookie(
        self,
        response: Response,
        user: "AdminUser",
        remember_me: bool = False,
    ) -> None:
        """
        Create a session cookie for authenticated user.

        Args:
            response: FastAPI Response object
            user: Authenticated admin user
            remember_me: Whether to create long-lived session
        """
        from opsdeck.auth.models import SessionData

        # Create session data
        session_data = SessionData.create(user, remember_me=remember_me)

        # Sign the session data
        token = self.signer.sign(session_data.model_dump(mode="json"))

        # Set cookie
        max_age = (
            SESSION_COOKIE_MAX_AGE_REMEMBER if remember_me else SESSION_COOKIE_MAX_AGE
        )

        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=token,
            max_age=max_age,
            httponly=True,  # Prevent JavaScript access
            secure=self.secure_cookies,
            samesite="lax",  # CSRF protection
        )

    def get_current_session(self, request: Request) -> Optional["SessionData"]:
        """
        Get current session data from cookie.

        Args:
            request: FastAPI Request object

        Returns:
            SessionData if valid session exists, None otherwise
        """
        from opsdeck.auth.models import SessionData

        token = request.cookies.get(SESSION_COOKIE_NAME)
        if not token:
            return None

        try:
            # Unsign and validate
            data = self.signer.unsign(token)
            session_data = SessionData(**data)

            # Check expiration
            if session_data.is_expired():
                return None

            return session_data

        except Exception:
            return None

    async def get_current_user(
        self,
        request: Request,
        session: "AsyncSession",
    ) -> Optional["AdminUser"]:
        """
        Get current authenticated user from session.

        Args:
            request: FastAPI Request object
            session: Database session

        Returns:
            AdminUser if authenticated, None otherwise
        """
        session_data = self.get_current_session(request)
        if not session_data:
            return None

        from sqlalchemy import select

        # Fetch user from database
        query = select(self.user_model).where(
            self.user_model.id == session_data.user_id,
            self.user_model.is_active,
        )
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        return user

    def logout(self, response: Response) -> None:
        """
        Logout user by clearing session cookie.

        Args:
            response: FastAPI Response object
        """
        response.delete_cookie(SESSION_COOKIE_NAME)

    def require_auth(self, request: Request) -> "SessionData":
        """
        Require authentication, raise 401 if not authenticated.

        Args:
            request: FastAPI Request object

        Returns:
            SessionData

        Raises:
            HTTPException: 401 if not authenticated

        Usage:
            session_data = auth_service.require_auth(request)
        """
        session_data = self.get_current_session(request)
        if not session_data:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Cookie"},
            )
        return session_data

    async def require_user(
        self,
        request: Request,
        session: "AsyncSession",
    ) -> "AdminUser":
        """
        Require authenticated user, raise 401 if not authenticated.

        Args:
            request: FastAPI Request object
            session: Database session

        Returns:
            AdminUser

        Raises:
            HTTPException: 401 if not authenticated
        """
        user = await self.get_current_user(request, session)
        if not user:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Cookie"},
            )
        return user

    async def require_roles(
        self,
        request: Request,
        session: "AsyncSession",
        roles: list[str],
    ) -> "AdminUser":
        """
        Require user with specific roles, raise 403 if unauthorized.

        Args:
            request: FastAPI Request object
            session: Database session
            roles: List of required roles

        Returns:
            AdminUser

        Raises:
            HTTPException: 401 if not authenticated, 403 if insufficient permissions
        """
        user = await self.require_user(request, session)

        if not user.has_any_role(roles):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return user
