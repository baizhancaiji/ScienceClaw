from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


OPENAI_COMPAT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


def normalize_openai_compat_base_url(base_url: str | None) -> str | None:
    """Normalize OpenAI-compatible API bases so bare hostnames target `/v1`."""
    if not base_url:
        return None

    trimmed = base_url.strip().rstrip("/")
    if not trimmed:
        return None

    parts = urlsplit(trimmed)
    path = parts.path.rstrip("/")
    if not path:
        path = "/v1"

    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))
