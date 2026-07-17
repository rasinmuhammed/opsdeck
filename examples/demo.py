"""
Example demo application for OpsDeck.

Run with: python -m examples.demo
Open: http://localhost:8000/admin
"""

from typing import Literal, Union

from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn

# Import from our library
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from opsdeck import OpsDeck


# --- Define Example Models ---


class User(BaseModel):
    """User model for demonstration."""

    id: int
    name: str
    email: str
    is_active: bool = True


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


# Discriminated Union - the key feature!
ContentBlock = Union[TextBlock, ImageBlock, VideoBlock]


class Article(BaseModel):
    """Article with polymorphic content blocks."""

    id: int
    title: str
    content: ContentBlock = Field(discriminator="type")
    published: bool = False


# --- Create FastAPI App ---

app = FastAPI(
    title="OpsDeck Demo",
    description="Example application demonstrating the admin interface",
)


# --- Initialize Admin ---

admin = OpsDeck(
    app,
    secret_key="your-super-secret-key-change-this",  # Must be 16+ chars
    title="Demo Admin",
)

# Register models
admin.register(
    User,
    list_display=["id", "name", "email", "is_active"],
    searchable_fields=["name", "email"],
    icon="users",
)

admin.register(
    Article,
    subtypes=[TextBlock, ImageBlock, VideoBlock],  # Enable polymorphic forms!
    list_display=["id", "title", "published"],
    icon="file-text",
)


# --- Regular API Routes ---


@app.get("/")
async def root():
    return {
        "message": "Welcome to OpsDeck Demo",
        "admin_url": "/admin",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
