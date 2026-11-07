"""JWT authentication with tenant claim extraction and role-based access control.

Tokens are validated using HS256 with a configurable secret. Tenant and role are
extracted from the token claims and enforced at every entry point.
"""
from __future__ import annotations
import hashlib
import hmac
import base64
import json
import time
from dataclasses import dataclass
from typing import Any


class AuthError(Exception):
    """Raised when a token is missing, malformed, expired, or claims are invalid."""


@dataclass(frozen=True)
class Principal:
    """Authenticated caller identity extracted from a verified JWT."""
    user_id: str
    tenant: str
    role: str

    def can(self, required_role: str) -> bool:
        """Role hierarchy: admin > reviewer > viewer."""
        hierarchy = {"viewer": 0, "reviewer": 1, "admin": 2}
        return hierarchy.get(self.role, -1) >= hierarchy.get(required_role, 99)


def _b64url_decode(segment: str) -> bytes:
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


def verify_token(token: str, secret: str, now: float | None = None) -> Principal:
    """Verify an HS256 JWT and return the authenticated Principal.

    Raises AuthError on any failure. Never trusts unverified claims.
    """
    if not token or not secret:
        raise AuthError("missing token or secret")
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthError("malformed token")
    header_b64, payload_b64, sig_b64 = parts
    try:
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
        sig = _b64url_decode(sig_b64)
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthError("malformed token") from exc
    if header.get("alg") != "HS256":
        raise AuthError("unsupported algorithm")
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        raise AuthError("signature verification failed")
    now = now if now is not None else time.time()
    exp = payload.get("exp")
    if exp is None or not isinstance(exp, (int, float)) or exp < now:
        raise AuthError("token expired or missing exp")
    tenant = payload.get("tenant")
    role = payload.get("role")
    user_id = payload.get("sub")
    if not tenant or not role or not user_id:
        raise AuthError("missing tenant, role, or sub claim")
    if role not in ("viewer", "reviewer", "admin"):
        raise AuthError("invalid role")
    return Principal(user_id=str(user_id), tenant=str(tenant), role=str(role))


def issue_token(user_id: str, tenant: str, role: str, secret: str, ttl_seconds: int = 3600, now: float | None = None) -> str:
    """Issue an HS256 JWT for local testing and integration. Production should use an IdP."""
    now_ts = now if now is not None else time.time()
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": user_id, "tenant": tenant, "role": role, "exp": now_ts + ttl_seconds, "iat": now_ts}
    h = base64.urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=").decode()
    sig = base64.urlsafe_b64encode(hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
    return f"{h}.{p}.{sig}"
