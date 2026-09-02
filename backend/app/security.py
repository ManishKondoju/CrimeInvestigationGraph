# backend/app/security.py - shared-secret gate for the public API.
#
# Every data endpoint hits Neo4j and /api/chat additionally spends Groq
# tokens per request, so an unauthenticated public deployment is a direct
# cost and data-exposure risk. The Next.js app calls this API from its
# server-side proxy route and attaches the key there, so the key is never
# shipped to the browser.
#
# The key is OPTIONAL: if API_KEY is unset the gate is disabled entirely,
# which keeps local development frictionless. It must be set in production.

import hmac
import os

from fastapi import Header, HTTPException, status

API_KEY_HEADER = "X-API-Key"


def _configured_key() -> str | None:
    key = os.getenv("API_KEY")
    return key.strip() if key and key.strip() else None


def require_api_key(x_api_key: str | None = Header(default=None, alias=API_KEY_HEADER)) -> None:
    """FastAPI dependency enforcing the shared secret when one is configured."""
    expected = _configured_key()

    # No key configured -> open (local dev). Production sets API_KEY.
    if expected is None:
        return

    # compare_digest avoids leaking key length/prefix through timing.
    if x_api_key is None or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": API_KEY_HEADER},
        )


def auth_enabled() -> bool:
    return _configured_key() is not None
