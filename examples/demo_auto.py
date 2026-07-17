"""
WOW Demo - Showcasing Auto-Discovery Magic

This is the "copy-paste and it works" demo that makes users say "WOW!

Run: python -m examples.demo_auto
Visit: http://localhost:8000/admin
"""

from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import String, Boolean, Integer, DateTime, Text, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import uvicorn

# Import from our library
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from opsdeck import OpsDeck


# --- SQLAlchemy Base ---


class Base(DeclarativeBase):
    pass


# --- Models (Just Define Them!) ---


class User(Base):
    """User model - will be auto-discovered!"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    articles = relationship("Article", back_populates="author")


class Category(Base):
    """Category model - will be auto-discovered!"""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Article(Base):
    """Article model - will be auto-discovered!"""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, published
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True
    )
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    author = relationship("User", back_populates="articles")


class Comment(Base):
    """Comment model - will be auto-discovered!"""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey("articles.id"))
    author_name: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# --- FastAPI App ---

app = FastAPI(
    title="OpsDeck - Auto-Discovery Demo",
    description="✨ Watch the magic happen!",
)

# Database
DATABASE_URL = "sqlite+aiosqlite:///./demo_auto.db"
engine = create_async_engine(DATABASE_URL, echo=True)


# --- THE MAGIC! ---
# Just 3 lines to get a full admin panel with all models!

admin = OpsDeck(
    app,
    engine=engine,
    secret_key="demo-secret-key-minimum-16-chars",
    title="🎯 Auto-Discovery Demo",
)

# ✨ MAGIC: Discovers User, Category, Article, Comment automatically!
models_registered = admin.auto_discover(Base)
print(f"✨ Auto-discovered and registered {models_registered} models!")

# That's it! No manual registration needed!


# --- Setup/Teardown ---


@app.on_event("startup")
async def startup():
    """Create tables and add sample data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("=" * 60)
    print("✅ Database tables created")
    print("✨ Models auto-discovered:")
    for model_name in admin.registry.get_all():
        config = admin.registry.get(model_name)
        print(f"   - {model_name}")
        print(f"     • List: {config.list_display}")
        print(f"     • Search: {config.searchable_fields}")
        print(f"     • Order: {config.ordering}")
    print("=" * 60)
    print("🚀 Admin interface: http://localhost:8000/admin")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown():
    """Clean up."""
    await engine.dispose()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Auto-Discovery Demo",
        "wow_factor": "✨ Zero configuration needed!",
        "models_discovered": models_registered,
        "admin_url": "/admin",
        "features": [
            "Auto-discovered all SQLAlchemy models",
            "Smart defaults for list_display",
            "Auto-detected searchable text fields",
            "Inferred sensible ordering",
            "Assigned icons based on model names",
        ],
        "try_it": "Visit /admin to see the magic!",
    }


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
