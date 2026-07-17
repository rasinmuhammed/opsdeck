"""
Simple Test Application for OpsDeck
Demonstrates basic usage with SQLAlchemy models
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from sqlalchemy import String, Integer, Boolean, Float, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from opsdeck import OpsDeck, AdminAction
from opsdeck.auth.models import AdminUserMixin, pwd_context


# SQLAlchemy Base
class Base(DeclarativeBase):
    pass


# Admin User Model
class User(AdminUserMixin, Base):
    __tablename__ = "users"


# Test Models
class Company(Base):
    """Company model"""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    employees: Mapped[list["Employee"]] = relationship(back_populates="company")

    def __admin_repr__(self):
        return self.name


class Employee(Base):
    """Employee model"""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150))
    salary: Mapped[float] = mapped_column(Float)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    company: Mapped["Company"] = relationship(back_populates="employees")

    def __admin_repr__(self):
        return f"{self.name} ({self.email})"


# Create async engine
engine = create_async_engine(
    "sqlite+aiosqlite:///./test_app.db",
    echo=False,
)


# Lifespan for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed data
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        # Create admin user
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                email="admin@test.com",
                password_hash=pwd_context.hash("admin123"),
                roles=["admin"],
                is_superuser=True,
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            print("✅ Created admin user: admin / admin123")

        # Seed test data
        result = await session.execute(select(Company))
        if not result.scalars().first():
            # Companies
            c1 = Company(name="TechCorp", industry="Technology", active=True)
            c2 = Company(name="FinanceHub", industry="Finance", active=True)
            session.add_all([c1, c2])
            await session.flush()

            # Employees
            employees = [
                Employee(
                    name="John Doe",
                    email="john@techcorp.com",
                    salary=85000,
                    company_id=c1.id,
                ),
                Employee(
                    name="Jane Smith",
                    email="jane@techcorp.com",
                    salary=95000,
                    company_id=c1.id,
                ),
                Employee(
                    name="Bob Johnson",
                    email="bob@financehub.com",
                    salary=78000,
                    company_id=c2.id,
                ),
            ]
            session.add_all(employees)
            await session.commit()
            print("✅ Seeded test data")

    yield  # App runs

    # Shutdown
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Test App - OpsDeck",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return RedirectResponse(url="/admin")


# Initialize OpsDeck
admin = OpsDeck(
    app,
    engine=engine,
    secret_key="test-secret-key-min-32-characters-long",
    title="Test Admin Panel",
)

# Register models
admin.register(
    Company,
    name="Companies",
    icon="briefcase",
    list_display=["id", "name", "industry", "active"],
    searchable_fields=["name", "industry"],
    filter_fields=["active", "industry"],
)


async def promote_employee(request, session, model, ids, user, config):
    from sqlalchemy import select
    from fastapi.responses import RedirectResponse

    if not ids:
        return RedirectResponse(
            url=request.url_for("admin:list", model="Employees"), status_code=303
        )

    stmt = select(model).where(model.id.in_([int(i) for i in ids]))
    result = await session.execute(stmt)
    employees = result.scalars().all()

    for emp in employees:
        if emp.salary:
            emp.salary += 10000
        else:
            emp.salary = 10000

    await session.commit()
    return RedirectResponse(
        url=request.url_for("admin:list", model="Employees"), status_code=303
    )


admin.register(
    Employee,
    name="Employees",
    icon="users",
    list_display=["id", "name", "email", "company", "salary", "active"],
    searchable_fields=["name", "email"],
    filter_fields=["active", "company"],
    actions=[
        AdminAction(
            name="promote",
            label="Promote Employee (+10k)",
            handler=promote_employee,
            confirmation_message="Are you sure you want to promote these employees? Their salaries will increase by $10,000.",
            bulk=True,
        )
    ],
)

admin.register(
    User,
    name="Admin Users",
    icon="shield",
    list_display=["username", "email", "is_active", "roles"],
    readonly=True,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8001, reload=True)
