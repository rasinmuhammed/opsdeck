"""
Demo app for recording GIF - shows auto-discovery in action.
"""

from fastapi import FastAPI
from sqlalchemy import String, Integer, Boolean, Text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from opsdeck import OpsDeck


# Models
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(Boolean, default=False)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[int] = mapped_column(Integer)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)


# Create FastAPI app
app = FastAPI(title="Demo App")

# Create async engine
engine = create_async_engine("sqlite+aiosqlite:///./demo.db", echo=False)

# Initialize admin with auto-discovery
admin = OpsDeck(
    app,
    engine=engine,
    secret_key="demo-secret-key-for-recording-only",
    title="FastAPI Shadcn Admin Demo",
)

# Auto-discover all models - ONE LINE!
admin.auto_discover(Base)


# Startup event to create tables
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Add sample data
    from sqlalchemy import select, func

    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        # Check if data exists
        result = await session.execute(select(func.count()).select_from(User))
        count = result.scalar()
        if count == 0:
            # Add sample users
            session.add_all(
                [
                    User(username="alice", email="alice@example.com", is_active=True),
                    User(username="bob", email="bob@example.com", is_active=True),
                    User(
                        username="charlie", email="charlie@example.com", is_active=False
                    ),
                ]
            )

            # Add sample articles
            session.add_all(
                [
                    Article(
                        title="Getting Started with FastAPI",
                        content="FastAPI is awesome...",
                        published=True,
                    ),
                    Article(
                        title="Building Admin Panels",
                        content="Admin panels are crucial...",
                        published=True,
                    ),
                    Article(
                        title="Draft Article",
                        content="This is a draft...",
                        published=False,
                    ),
                ]
            )

            # Add sample products
            session.add_all(
                [
                    Product(name="Laptop", price=999, in_stock=True),
                    Product(name="Mouse", price=29, in_stock=True),
                    Product(name="Keyboard", price=79, in_stock=False),
                ]
            )

            await session.commit()


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("🚀 FastAPI Shadcn Admin Demo")
    print("=" * 60)
    print("\nAuto-discovered models:")
    print("  ✓ User")
    print("  ✓ Article")
    print("  ✓ Product")
    print("\n📍 Admin panel: http://localhost:8000/admin")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
