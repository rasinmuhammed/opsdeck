"""
Live demo for Vercel - OpsDeck.
Showcases Matrix UI theme and auto_discover feature
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from sqlalchemy import String, Integer, Boolean, Text, Float, ForeignKey, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from opsdeck import OpsDeck
from opsdeck.audit.models import AuditLog as AuditLogMixin

# Import Auth components
from opsdeck.auth.models import AdminUserMixin, pwd_context


# SQLAlchemy Base
class Base(DeclarativeBase):
    pass


# Define the Admin User model
class User(AdminUserMixin, Base):
    __tablename__ = "users"


# Demo Models - Showcase auto_discover
class BlogPost(Base):
    """Blog posts with title, content, and author"""

    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)

    # Relationship Showcase (Smart Select)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["Author"] = relationship(back_populates="posts")

    published: Mapped[bool] = mapped_column(Boolean, default=False)
    views: Mapped[int] = mapped_column(Integer, default=0)

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=True)
    category: Mapped["Category"] = relationship()

    def __admin_repr__(self):
        return self.title


class Product(Base):
    """E-commerce products"""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer)
    available: Mapped[bool] = mapped_column(Boolean, default=True)


class Author(Base):
    """Author profiles"""

    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150))
    bio: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    posts: Mapped[list["BlogPost"]] = relationship(back_populates="author")

    def __admin_repr__(self):
        return f"{self.name} ({self.email})"


class Category(Base):
    """Content categories"""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


# Create async SQLite engine
engine = create_async_engine(
    "sqlite+aiosqlite:///./demo.db",
    echo=False,
    connect_args={"check_same_thread": False},
)


# Lifespan context for startup/shutdown (serverless compatible)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Force fresh database on startup (for demo purposes)
    # Using drop_all + create_all is more reliable than file deletion
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        print("🔄 Reset database - dropped and recreated all tables")

    # Seed demo data
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        # Check if users exist (Seed Admin)
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=pwd_context.hash("admin"),
                roles=["admin"],
                is_superuser=True,
                is_active=True,
            )
            session.add(admin_user)
            await session.commit()
            print("✅ Created default admin user: admin/admin")

        # Check if data exists
        result = await session.execute(select(BlogPost))
        if not result.scalars().first():
            # Create Authors
            a1 = Author(
                name="Neo",
                email="neo@matrix.com",
                bio="The One.",
                active=True,
            )
            a2 = Author(
                name="Trinity",
                email="trinity@matrix.com",
                bio="Legendary hacker.",
                active=True,
            )
            session.add_all([a1, a2])
            await session.flush()

            # Create Categories
            c1 = Category(name="Tech", description="Technology news")
            c2 = Category(name="Philosophy", description="Deep thoughts")
            session.add_all([c1, c2])
            await session.flush()

            # Create Posts
            p1 = BlogPost(
                title="Wake Up",
                content="The Matrix has you...",
                published=True,
                views=100,
                author_id=a1.id,
                category_id=c1.id,
            )
            p2 = BlogPost(
                title="Follow the White Rabbit",
                content="Knock, knock, Neo.",
                published=True,
                views=50,
                author_id=a1.id,
                category_id=c2.id,
            )
            session.add_all([p1, p2])

            # Create Products
            items = [
                Product(
                    name="Red Pill",
                    description="Wake up from the Matrix.",
                    price=99.99,
                    stock=100,
                    available=True,
                ),
                Product(
                    name="Blue Pill",
                    description="Stay in wonderland.",
                    price=0.00,
                    stock=1000,
                    available=True,
                ),
                Product(
                    name="Sunglasses",
                    description="Essential cyberpunk accessory.",
                    price=150.00,
                    stock=50,
                    available=True,
                ),
                Product(
                    name="Premium Laptop",
                    description="High-performance machine.",
                    price=1299.99,
                    stock=15,
                    available=True,
                ),
                Product(
                    name="Mechanical Keyboard",
                    description="Clicky keys for coding.",
                    price=159.99,
                    stock=32,
                    available=True,
                ),
            ]
            session.add_all(items)

            # Add demo categories
            session.add_all(
                [
                    Category(
                        name="Technology",
                        description="Articles about software development.",
                        active=True,
                    ),
                    Category(
                        name="Design",
                        description="UI/UX design.",
                        active=True,
                    ),
                ]
            )

            await session.commit()
            print("✅ Demo data seeded!")

    yield  # App runs here

    # Shutdown (cleanup if needed)
    await engine.dispose()


# Create FastAPI app with lifespan
app = FastAPI(
    title="OpsDeck - Live Demo",
    description="Showcasing Matrix UI and Auto-Discovery",
    version="1.0.0",
    lifespan=lifespan,
)


# Redirect root to admin
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/admin")


# Initialize admin
admin = OpsDeck(
    app,
    engine=engine,
    secret_key="demo-live-key-for-render-deployment",
    title="OpsDeck Demo",
    demo_mode=True,
)

# 🎯 Explicit Registration to Showcase Features

# 1. Authors: Simple configuration
admin.register(
    Author,
    name="Authors",
    icon="users",
    list_display=["name", "email", "active"],
    searchable_fields=["name", "email"],
    filter_fields=["active"],
)

# 2. Blog Posts: Showcase Relationships & Advanced Filters
admin.register(
    BlogPost,
    name="Blog Posts",
    icon="file-text",
    list_display=["title", "author", "published", "views"],
    searchable_fields=["title"],
    filter_fields=["published", "author"],
)

# 3. Products: Numeric Filtering
admin.register(
    Product,
    name="Products",
    icon="shopping-cart",
    list_display=["name", "price", "stock", "available"],
    filter_fields=["available", "price"],
)

# 4. Categories: Auto-discover fallback (or simple reg)
admin.register(Category, icon="tag")

# 5. Admin Users & Audit Logs (System)


# Create concrete AuditLog model
class AuditLog(AuditLogMixin, Base):
    __tablename__ = "audit_logs"


admin.register(
    User,
    name="System Users",
    icon="shield",
    list_display=["username", "email", "roles", "is_active", "last_login"],
    searchable_fields=["username", "email"],
    filter_fields=["is_active", "roles"],
    readonly=True,  # Protect admin user for now
)

admin.register(
    AuditLog,
    name="Audit Logs",
    icon="activity",
    list_display=["action", "model_name", "record_id", "user_id", "created_at"],
    searchable_fields=["model_name", "action", "record_id"],
    filter_fields=["action", "model_name"],
    ordering=["-created_at"],
    readonly=True,
)


# Entry point for Render/local
if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
