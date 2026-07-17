"""
Audit Logging for FastAPI Shadcn Admin.

Tracks all CRUD operations with user context, IP addresses, and field-level changes.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum

from sqlalchemy import String, Integer, DateTime, JSON as SQLJSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AuditAction(str, Enum):
    """Audit action types."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"  # Optional: track views for sensitive models


class AuditLog(DeclarativeBase):
    """
    Audit log model for tracking all changes.

    Stores who changed what, when, and from where.

    Usage:
        from opsdeck.audit.models import AuditLog
        from sqlalchemy.orm import declarative_base

        Base = declarative_base()

        class AdminAuditLog(AuditLog, Base):
            __tablename__ = "audit_logs"
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # User context
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Action details
    action: Mapped[str] = mapped_column(
        String(20), index=True
    )  # create, update, delete
    model_name: Mapped[str] = mapped_column(String(100), index=True)
    record_id: Mapped[str] = mapped_column(String(100), index=True)

    # Changes (field-level tracking)
    changes: Mapped[Optional[Dict[str, Any]]] = mapped_column(SQLJSON, nullable=True)
    # Format: {"field_name": {"old": "value", "new": "value"}}

    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    @classmethod
    def format_changes(
        cls, old_data: Dict[str, Any], new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format field-level changes for logging.

        Args:
            old_data: Old record data
            new_data: New record data

        Returns:
            Dict of changed fields with old and new values
        """
        changes = {}
        all_fields = set(old_data.keys()) | set(new_data.keys())

        for field in all_fields:
            old_val = old_data.get(field)
            new_val = new_data.get(field)

            # Skip if unchanged
            if old_val == new_val:
                continue

            # Skip internal fields
            if field.startswith("_"):
                continue

            changes[field] = {
                "old": cls._serialize_value(old_val),
                "new": cls._serialize_value(new_val),
            }

        return changes

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialize value for JSON storage."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (list, dict)):
            return value
        if hasattr(value, "__dict__"):
            # SQLAlchemy model
            return str(value)
        return value


class AuditLogger:
    """Service for creating audit log entries."""

    def __init__(self, audit_model: type[AuditLog]):
        """
        Initialize audit logger.

        Args:
            audit_model: AuditLog model class
        """
        self.audit_model = audit_model

    async def log_create(
        self,
        session: "AsyncSession",
        model_name: str,
        record_id: str,
        record_data: Dict[str, Any],
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Log a CREATE operation.

        Args:
            session: Database session
            model_name: Name of the model
            record_id: ID of created record
            record_data: Data of created record
            user_id: ID of user who created
            username: Username who created
            ip_address: IP address of request
            user_agent: User agent string
        """
        log_entry = self.audit_model(
            user_id=user_id,
            username=username,
            action=AuditAction.CREATE,
            model_name=model_name,
            record_id=str(record_id),
            changes=record_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        session.add(log_entry)

    async def log_update(
        self,
        session: "AsyncSession",
        model_name: str,
        record_id: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Log an UPDATE operation.

        Args:
            session: Database session
            model_name: Name of the model
            record_id: ID of updated record
            old_data: Data before update
            new_data: Data after update
            user_id: ID of user who updated
            username: Username who updated
            ip_address: IP address of request
            user_agent: User agent string
        """
        changes = self.audit_model.format_changes(old_data, new_data)

        # Only log if there are actual changes
        if not changes:
            return

        log_entry = self.audit_model(
            user_id=user_id,
            username=username,
            action=AuditAction.UPDATE,
            model_name=model_name,
            record_id=str(record_id),
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        session.add(log_entry)

    async def log_delete(
        self,
        session: "AsyncSession",
        model_name: str,
        record_id: str,
        record_data: Dict[str, Any],
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Log a DELETE operation.

        Args:
            session: Database session
            model_name: Name of the model
            record_id: ID of deleted record
            record_data: Data of deleted record
            user_id: ID of user who deleted
            username: Username who deleted
            ip_address: IP address of request
            user_agent: User agent string
        """
        log_entry = self.audit_model(
            user_id=user_id,
            username=username,
            action=AuditAction.DELETE,
            model_name=model_name,
            record_id=str(record_id),
            changes=record_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        session.add(log_entry)

    def get_request_context(self, request) -> Dict[str, Optional[str]]:
        """
        Extract request context for audit logging.

        Args:
            request: FastAPI Request object

        Returns:
            Dict with ip_address and user_agent
        """
        # Get IP address (handle proxies)
        ip = None
        if "x-forwarded-for" in request.headers:
            ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        elif "x-real-ip" in request.headers:
            ip = request.headers["x-real-ip"]
        else:
            ip = request.client.host if request.client else None

        # Get user agent
        user_agent = request.headers.get("user-agent")

        return {
            "ip_address": ip,
            "user_agent": user_agent[:500] if user_agent else None,  # Truncate
        }
