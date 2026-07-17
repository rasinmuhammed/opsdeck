"""
Enhanced Demo Application with Database Integration

Run with: python -m examples.demo_db
Open: http://localhost:8000/admin
"""

from typing import Literal, Union
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel, Field
from sqlalchemy import String, Boolean, Integer, DateTime, Text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uvicorn

# Import from our library
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from opsdeck import OpsDeck


# --- SQLAlchemy Base ---


class Base(DeclarativeBase):
    pass


# --- SQLAlchemy Models ---


class User(Base):
    """User model with database persistence."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Article(Base):
    """Article model for content management."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# --- Pydantic Models for Polymorphic Forms ---
# These demonstrate the discriminated union feature


class TextBlock(BaseModel):
    """Text content block."""

    type: Literal["text"] = "text"
    content: str
    font_size: int = 16


class ImageBlock(BaseModel):
    """Image content block."""

    type: Literal["image"] = "image"
    url: str
    alt_text: str
    width: int | None = None
    height: int | None = None


class VideoBlock(BaseModel):
    """Video content block."""

    type: Literal["video"] = "video"
    url: str
    duration: int
    autoplay: bool = False


# Discriminated Union - the key polymorphic feature!
ContentBlock = Union[TextBlock, ImageBlock, VideoBlock]


class Content(BaseModel):
    """Content with polymorphic blocks (Pydantic-only, no database)."""

    id: int
    title: str
    content_block: ContentBlock = Field(discriminator="type")


# --- Create FastAPI App ---

app = FastAPI(
    title="OpsDeck - Production Demo",
    description="Full-featured admin with database integration",
)


# --- Database Setup ---

# Using SQLite for demo (switch to PostgreSQL for production)
DATABASE_URL = "sqlite+aiosqlite:///./fastapi_admin_demo.db"
# For PostgreSQL: "postgresql+asyncpg://user:pass@localhost/dbname"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log SQL queries
    future=True,
)


# --- Initialize Admin with Database ---

admin = OpsDeck(
    app,
    engine=engine,  # NEW: Pass database engine
    secret_key="production-secret-key-change-this-min-16-chars",
    title="Production Admin",
)


# Register SQLAlchemy models (these will have real CRUD operations)
admin.register(
    User,
    list_display=["id", "name", "email", "is_active", "created_at"],
    searchable_fields=["name", "email"],
    ordering=["-created_at"],
    icon="users",
)

admin.register(
    Article,
    list_display=["id", "title", "published", "created_at"],
    searchable_fields=["title", "content"],
    ordering=["-created_at"],
    icon="file-text",
)


# Register Pydantic model (no database, shows polymorphic forms only)
admin.register(
    Content,
    subtypes=[TextBlock, ImageBlock, VideoBlock],  # Polymorphic feature
    icon="layers",
    readonly=True,  # Pydantic-only, no database
)


# --- Startup/Shutdown Events ---


@app.on_event("startup")
async def startup():
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")
    print("🚀 Admin interface: http://localhost:8000/admin")


@app.on_event("shutdown")
async def shutdown():
    """Close database connections on shutdown."""
    await engine.dispose()
    print("👋 Database connections closed")


# --- Regular API Routes ---


@app.get("/")
async def root():
    return {
        "message": "OpsDeck - Production Demo",
        "features": [
            "✅ Real database integration (SQLite)",
            "✅ Full CRUD operations",
            "✅ Pagination & search",
            "✅ Security (signed tokens, CSRF, CSP)",
            "✅ Polymorphic forms (discriminated unions)",
        ],
        "admin_url": "/admin",
        "docs_url": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "database": "connected"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
