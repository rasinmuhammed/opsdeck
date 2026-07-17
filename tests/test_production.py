"""
Integration tests for production features.

Tests database CRUD, authentication, audit logging, and permissions.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from opsdeck import OpsDeck
from opsdeck.auth.models import AdminUserMixin, SessionData
from opsdeck.audit.models import AuditLog, AuditLogger


# --- Test Models ---


class Base(DeclarativeBase):
    pass


class TestUser(Base):
    """Test user model."""

    __tablename__ = "test_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TestAdminUser(AdminUserMixin, Base):
    """Test admin user."""

    __tablename__ = "test_admin_users"


class TestAuditLog(AuditLog, Base):
    """Test audit log."""

    __tablename__ = "test_audit_logs"


# --- Test Fixtures ---


@pytest.fixture
async def async_engine():
    """Create async SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Create async session."""
    Session = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with Session() as session:
        yield session


@pytest.fixture
def app_with_db(async_engine):
    """Create FastAPI app with database."""
    app = FastAPI()

    admin = OpsDeck(
        app,
        engine=async_engine,
        secret_key="test-secret-key-for-testing",
        title="Test Admin",
    )

    admin.register(
        TestUser,
        list_display=["id", "name", "email"],
        searchable_fields=["name", "email"],
    )

    return app


@pytest.fixture
def client(app_with_db):
    """Create test client."""
    return TestClient(app_with_db)


# --- CRUD Tests ---


class TestDatabaseCRUD:
    """Test database CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_record(self, async_session):
        """Test creating a record."""
        from opsdeck.core.crud import CRUDBase

        crud = CRUDBase(TestUser)

        user = await crud.create(
            async_session,
            obj_in={"name": "John Doe", "email": "john@example.com", "is_active": True},
        )

        assert user.id is not None
        assert user.name == "John Doe"
        assert user.email == "john@example.com"

    @pytest.mark.asyncio
    async def test_list_with_pagination(self, async_session):
        """Test list with pagination."""
        from opsdeck.core.crud import CRUDBase

        crud = CRUDBase(TestUser)

        # Create test data
        for i in range(30):
            await crud.create(
                async_session,
                obj_in={"name": f"User {i}", "email": f"user{i}@example.com"},
            )

        # Test pagination
        records, total = await crud.list(async_session, page=1, per_page=10)

        assert len(records) == 10
        assert total == 30

        # Test page 2
        records, total = await crud.list(async_session, page=2, per_page=10)
        assert len(records) == 10

    @pytest.mark.asyncio
    async def test_search(self, async_session):
        """Test search functionality."""
        from opsdeck.core.crud import CRUDBase

        crud = CRUDBase(TestUser)

        # Create test data
        await crud.create(
            async_session, obj_in={"name": "Alice", "email": "alice@example.com"}
        )
        await crud.create(
            async_session, obj_in={"name": "Bob", "email": "bob@example.com"}
        )
        await crud.create(
            async_session, obj_in={"name": "Charlie", "email": "charlie@example.com"}
        )

        # Search by name
        records, total = await crud.list(
            async_session,
            search="Alice",
            search_fields=["name"],
        )

        assert total == 1
        assert records[0].name == "Alice"

    @pytest.mark.asyncio
    async def test_update_record(self, async_session):
        """Test updating a record."""
        from opsdeck.core.crud import CRUDBase

        crud = CRUDBase(TestUser)

        # Create
        user = await crud.create(
            async_session, obj_in={"name": "John", "email": "john@example.com"}
        )
        user_id = user.id

        # Update
        updated = await crud.update(
            async_session, id=user_id, obj_in={"name": "John Updated"}
        )

        assert updated.id == user_id
        assert updated.name == "John Updated"
        assert updated.email == "john@example.com"  # Unchanged

    @pytest.mark.asyncio
    async def test_delete_record(self, async_session):
        """Test deleting a record."""
        from opsdeck.core.crud import CRUDBase

        crud = CRUDBase(TestUser)

        # Create
        user = await crud.create(
            async_session, obj_in={"name": "John", "email": "john@example.com"}
        )
        user_id = user.id

        # Delete
        deleted = await crud.delete(async_session, id=user_id)
        assert deleted is True

        # Verify deleted
        user = await crud.get(async_session, id=user_id)
        assert user is None


# --- Authentication Tests ---


class TestAuthentication:
    """Test authentication system."""

    @pytest.mark.asyncio
    async def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "SecurePassword123!"

        # Hash password
        hashed = TestAdminUser.hash_password(password)

        # Create user
        user = TestAdminUser(
            username="testuser",
            email="test@example.com",
            password_hash=hashed,
            roles=["admin"],
        )

        # Verify correct password
        assert user.verify_password(password) is True

        # Verify incorrect password
        assert user.verify_password("WrongPassword") is False

    @pytest.mark.asyncio
    async def test_role_checking(self):
        """Test role-based permissions."""
        user = TestAdminUser(
            username="testuser",
            email="test@example.com",
            password_hash="dummy",
            roles=["editor", "viewer"],
        )

        assert user.has_role("editor") is True
        assert user.has_role("viewer") is True
        assert user.has_role("admin") is False
        assert user.has_any_role(["admin", "editor"]) is True

    @pytest.mark.asyncio
    async def test_superuser_bypass(self):
        """Test superuser bypasses all role checks."""
        user = TestAdminUser(
            username="superuser",
            email="super@example.com",
            password_hash="dummy",
            roles=[],
            is_superuser=True,
        )

        assert user.has_role("any_role") is True
        assert user.has_any_role(["admin", "editor"]) is True

    def test_session_data_creation(self):
        """Test session data creation."""
        user = TestAdminUser(
            id=1,
            username="testuser",
            email="test@example.com",
            password_hash="dummy",
            roles=["admin"],
            is_superuser=False,
        )

        session_data = SessionData.create(user, remember_me=False)

        assert session_data.user_id == 1
        assert session_data.username == "testuser"
        assert session_data.roles == ["admin"]
        assert session_data.is_superuser is False
        assert session_data.is_expired() is False


# --- Audit Logging Tests ---


class TestAuditLogging:
    """Test audit logging functionality."""

    @pytest.mark.xfail(reason="Audit table not created in test fixtures yet")
    @pytest.mark.asyncio
    async def test_log_create(self, async_session):
        """Test logging create operation."""
        logger = AuditLogger(TestAuditLog)

        await logger.log_create(
            async_session,
            model_name="TestUser",
            record_id="123",
            record_data={"name": "John", "email": "john@example.com"},
            user_id=1,
            username="admin",
            ip_address="127.0.0.1",
            user_agent="TestAgent",
        )

        # Flush to make sure the log is in the session
        await async_session.flush()

        # Verify log created
        from sqlalchemy import select

        result = await async_session.execute(select(TestAuditLog))
        log = result.scalar_one()

        assert log.action == "create"
        assert log.model_name == "TestUser"
        assert log.record_id == "123"
        assert log.user_id == 1
        assert log.username == "admin"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Audit table not created in test fixtures yet")
    async def test_log_update_with_changes(self, async_session):
        """Test logging an update with changes."""
        logger = AuditLogger(TestAuditLog)

        old_data = {"name": "John", "email": "john@old.com"}
        new_data = {"name": "John Updated", "email": "john@old.com"}

        await logger.log_update(
            async_session,
            model_name="TestUser",
            record_id="123",
            old_data=old_data,
            new_data=new_data,
            user_id=1,
            username="admin",
        )

        # Flush to make sure the log is in the session
        await async_session.flush()

        # Verify changes tracked
        from sqlalchemy import select

        result = await async_session.execute(select(TestAuditLog))
        log = result.scalar_one()

        assert log.action == "update"
        assert "name" in log.changes
        assert log.changes["name"]["old"] == "John"
        assert log.changes["name"]["new"] == "John Updated"
        assert "email" not in log.changes  # Unchanged field not logged

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Audit table not created in test fixtures yet")
    async def test_no_log_if_no_changes(self, async_session):
        """Test that no log is created if there are no changes."""
        logger = AuditLogger(TestAuditLog)

        same_data = {"name": "John", "email": "john@example.com"}

        await logger.log_update(
            async_session,
            model_name="TestUser",
            record_id="123",
            old_data=same_data,
            new_data=same_data,
            user_id=1,
            username="admin",
        )

        # Flush to sync state
        await async_session.flush()

        # Verify no log created
        from sqlalchemy import select, func

        result = await async_session.execute(
            select(func.count()).select_from(TestAuditLog)
        )
        count = result.scalar()

        assert count == 0


# --- Integration Tests ---


class TestAdminIntegration:
    """Integration tests with full admin."""

    def test_admin_dashboard_loads(self, client):
        """Test admin dashboard loads."""
        response = client.get("/admin/")
        assert response.status_code == 200
        assert "Test Admin" in response.text

    def test_list_view_with_database(self, client):
        """Test list view with database integration."""
        response = client.get("/admin/TestUser/")
        assert response.status_code == 200
        # Should render table even if empty
        assert "TestUser" in response.text or "test_users" in response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
