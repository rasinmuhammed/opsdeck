"""
Security module for FastAPI Shadcn Admin.

Implements:
- URLSigner: Signed tokens for Anti-IDOR protection
- CSPMiddleware: Content Security Policy with per-request nonces
"""

from __future__ import annotations

import secrets
from typing import Any

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SignatureError(Exception):
    """Raised when URL signature validation fails."""

    pass


class URLSigner:
    """
    Secure URL token signer using itsdangerous.

    Creates signed tokens containing intent (model, action, id) to prevent
    IDOR attacks. Tokens are time-limited and tamper-proof.

    Usage:
        signer = URLSigner("secret-key")
        token = signer.sign({"model": "User", "action": "load_fragment", "id": 1})
        payload = signer.unsign(token)  # Validates and returns original payload
    """

    DEFAULT_MAX_AGE = 3600  # 1 hour

    def __init__(self, secret_key: str, salt: str = "fastapi-shadcn-admin"):
        """
        Initialize the URL signer.

        Args:
            secret_key: Secret key for signing. Must be kept secure.
            salt: Additional salt for the signature (default: "fastapi-shadcn-admin")
        """
        if not secret_key or len(secret_key) < 16:
            raise ValueError("Secret key must be at least 16 characters long")

        self._serializer = URLSafeTimedSerializer(secret_key, salt=salt)

    def sign(self, payload: dict[str, Any]) -> str:
        """
        Create a signed token from the payload.

        Args:
            payload: Dictionary containing intent data (model, action, id, etc.)

        Returns:
            URL-safe signed token string
        """
        return self._serializer.dumps(payload)

    def unsign(self, token: str, max_age: int | None = None) -> dict[str, Any]:
        """
        Validate and decode a signed token.

        Args:
            token: The signed token to validate
            max_age: Maximum age in seconds (default: 3600)

        Returns:
            The original payload dictionary

        Raises:
            SignatureError: If token is invalid, expired, or tampered with
        """
        if max_age is None:
            max_age = self.DEFAULT_MAX_AGE

        try:
            payload = self._serializer.loads(token, max_age=max_age)
            if not isinstance(payload, dict):
                raise SignatureError("Invalid payload format")
            return payload
        except SignatureExpired:
            raise SignatureError("Token has expired")
        except BadSignature:
            raise SignatureError("Invalid or tampered token")

    def create_fragment_token(
        self,
        model: str,
        action: str = "load_fragment",
        subtype: str | None = None,
        record_id: int | str | None = None,
    ) -> str:
        """
        Create a signed token for fragment loading.

        Args:
            model: The model name
            action: The action (default: "load_fragment")
            subtype: Optional subtype for polymorphic models
            record_id: Optional record ID for edit operations

        Returns:
            Signed token string
        """
        payload = {
            "model": model,
            "action": action,
        }
        if subtype:
            payload["subtype"] = subtype
        if record_id is not None:
            payload["id"] = record_id

        return self.sign(payload)


class CSPMiddleware(BaseHTTPMiddleware):
    """
    Content Security Policy Middleware with per-request nonces.

    Generates a cryptographic nonce for every request and injects it into:
    1. The CSP header (script-src 'nonce-xxx')
    2. The request state (for template usage)

    This prevents XSS attacks by ensuring only scripts with the correct
    nonce can execute.
    """

    NONCE_LENGTH = 32  # 256 bits of entropy

    def __init__(self, app, policy: dict[str, str] | None = None):
        """
        Initialize CSP middleware.

        Args:
            app: The ASGI application
            policy: Optional custom CSP directives. Defaults to a secure policy.
        """
        super().__init__(app)
        self._base_policy = policy or self._default_policy()

    @staticmethod
    def _default_policy() -> dict[str, str]:
        """Return the default secure CSP policy."""
        return {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-eval' https://cdn.tailwindcss.com https://cdn.jsdelivr.net",  # Nonce will be appended
            "style-src": "'self' 'unsafe-inline' https://cdn.tailwindcss.com https://fonts.googleapis.com",
            "img-src": "'self' data: https:",
            "font-src": "'self' https://fonts.gstatic.com",
            "connect-src": "'self'",
            "frame-ancestors": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
        }

    def _generate_nonce(self) -> str:
        """Generate a cryptographically secure nonce."""
        return secrets.token_urlsafe(self.NONCE_LENGTH)

    def _build_csp_header(self, nonce: str) -> str:
        """Build the CSP header string with the nonce."""
        policy = self._base_policy.copy()

        # Add nonce to script-src
        policy["script-src"] = f"{policy['script-src']} 'nonce-{nonce}'"

        # Build the header string
        directives = [f"{key} {value}" for key, value in policy.items()]
        return "; ".join(directives)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and add CSP headers."""
        # Generate nonce for this request
        nonce = self._generate_nonce()

        # Store nonce in request state for template access
        request.state.csp_nonce = nonce

        # Process the request
        response = await call_next(request)

        # Add CSP header to response
        csp_header = self._build_csp_header(nonce)
        response.headers["Content-Security-Policy"] = csp_header

        # Additional security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


def get_csp_nonce(request: Request) -> str:
    """
    Get the CSP nonce from the request state.

    Args:
        request: The Starlette request object

    Returns:
        The nonce string for this request

    Raises:
        AttributeError: If CSP middleware is not installed
    """
    return getattr(request.state, "csp_nonce", "")
