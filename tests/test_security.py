"""
Security Tests for FastAPI Shadcn Admin

Tests the security architecture:
- Signed URL tokens (Anti-IDOR)
- Strict model registry (Anti-Type-Confusion)
- Unregistered model rejection
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import Literal

# Import from our library
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from opsdeck import OpsDeck
from opsdeck.core.security import URLSigner, SignatureError
from opsdeck.core.registry import (
    AdminRegistry,
    ModelNotFoundError,
    SubtypeNotAllowedError,
)


# --- Test Models ---


class User(BaseModel):
    id: int
    name: str
    email: str


class TextBlock(BaseModel):
    type: Literal["text"] = "text"
    content: str


class ImageBlock(BaseModel):
    type: Literal["image"] = "image"
    url: str


class VideoBlock(BaseModel):
    """Not registered - should be rejected."""

    type: Literal["video"] = "video"
    url: str


# --- URLSigner Tests ---


class TestURLSigner:
    """Tests for the URLSigner class."""

    def test_sign_and_unsign(self):
        """Test that signed tokens can be validated."""
        signer = URLSigner("test-secret-key-1234")
        payload = {"model": "User", "action": "load_fragment"}

        token = signer.sign(payload)
        result = signer.unsign(token)

        assert result == payload

    def test_invalid_token_raises_error(self):
        """Test that tampered tokens are rejected."""
        signer = URLSigner("test-secret-key-1234")

        with pytest.raises(SignatureError):
            signer.unsign("invalid-token")

    def test_expired_token_raises_error(self):
        """Test that expired tokens are rejected."""
        import time

        signer = URLSigner("test-secret-key-1234")
        payload = {"model": "User"}
        token = signer.sign(payload)

        # Wait 2 seconds and use max_age=1 to force expiration
        time.sleep(2)
        with pytest.raises(SignatureError):
            signer.unsign(token, max_age=1)

    def test_short_secret_key_raises_error(self):
        """Test that short secret keys are rejected."""
        with pytest.raises(ValueError):
            URLSigner("short")

    def test_create_fragment_token(self):
        """Test fragment token creation."""
        signer = URLSigner("test-secret-key-1234")
        token = signer.create_fragment_token(
            model="Article",
            action="load_fragment",
            subtype="TextBlock",
        )

        payload = signer.unsign(token)
        assert payload["model"] == "Article"
        assert payload["action"] == "load_fragment"
        assert payload["subtype"] == "TextBlock"


# --- AdminRegistry Tests ---


class TestAdminRegistry:
    """Tests for the AdminRegistry class."""

    def test_register_model(self):
        """Test model registration."""
        registry = AdminRegistry()
        registry.register(User, list_display=["id", "name"])

        assert "User" in registry
        assert registry.is_registered("User")

    def test_unregistered_model_raises_error(self):
        """Test that accessing unregistered models raises error."""
        registry = AdminRegistry()

        with pytest.raises(ModelNotFoundError):
            registry.get("UnregisteredModel")

    def test_validate_model_access(self):
        """Test model access validation."""
        registry = AdminRegistry()
        registry.register(User)

        config = registry.validate_model_access("User")
        assert config.model == User

    def test_validate_model_access_fails_for_unregistered(self):
        """Test that unregistered models fail validation."""
        registry = AdminRegistry()

        with pytest.raises(ModelNotFoundError):
            registry.validate_model_access("Secret")

    def test_register_with_subtypes(self):
        """Test registration with subtypes."""
        registry = AdminRegistry()
        registry.register(
            User,  # Using User as parent for simplicity
            name="ContentBlock",
            subtypes=[TextBlock, ImageBlock],
        )

        config = registry.get("ContentBlock")
        assert config.is_subtype_allowed("TextBlock")
        assert config.is_subtype_allowed("ImageBlock")
        assert not config.is_subtype_allowed("VideoBlock")

    def test_validate_subtype_access_success(self):
        """Test subtype validation for allowed subtypes."""
        registry = AdminRegistry()
        registry.register(User, name="Content", subtypes=[TextBlock, ImageBlock])

        subtype = registry.validate_subtype_access("Content", "TextBlock")
        assert subtype == TextBlock

    def test_validate_subtype_access_fails_for_unregistered(self):
        """Test that unregistered subtypes fail validation."""
        registry = AdminRegistry()
        registry.register(User, name="Content", subtypes=[TextBlock, ImageBlock])

        # VideoBlock is not in subtypes list
        with pytest.raises(SubtypeNotAllowedError):
            registry.validate_subtype_access("Content", "VideoBlock")


# --- Integration Tests ---


class TestAdminIntegration:
    """Integration tests for the full admin."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app with admin."""
        app = FastAPI()
        admin = OpsDeck(
            app,
            secret_key="test-secret-key-for-testing",
            title="Test Admin",
        )
        admin.register(User)
        admin.register(
            User,
            name="ContentBlock",
            subtypes=[TextBlock, ImageBlock],
        )
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_unregistered_model_returns_403(self, client):
        """CRITICAL: Unregistered model access must return 403."""
        response = client.get("/admin/SecretModel/")
        assert response.status_code == 403

    def test_invalid_fragment_token_returns_403(self, client):
        """Test that invalid fragment tokens are rejected."""
        response = client.get("/admin/fragments?token=invalid-token")
        assert response.status_code == 403

    def test_dashboard_loads(self, client):
        """Test that dashboard loads successfully."""
        response = client.get("/admin/")
        assert response.status_code == 200
        assert "Test Admin" in response.text

    def test_list_view_loads_for_registered_model(self, client):
        """Test list view for registered model."""
        response = client.get("/admin/User/")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
