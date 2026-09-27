"""Customer / tenant resolver (base product).

Resolution order (aligned with AI-SDR frontend backendResolver pattern):
1. Explicit X-Customer-Id header (demo / API clients)
2. Host map (customer-1.localhost → customer-1)
3. Platform default customer
"""

from __future__ import annotations


def normalize_host(host: str | None) -> str:
    base = str(host or "").replace(" ", "").lower()
    # strip port
    if ":" in base:
        base = base.split(":", 1)[0]
    if base.startswith("www."):
        base = base[4:]
    return base


def resolve_customer(
    *,
    explicit_id: str | None,
    host: str | None,
    host_map: dict[str, str],
    default_customer_id: str,
) -> str:
    if explicit_id:
        return explicit_id.strip().lower()

    normalized = normalize_host(host)
    if normalized in host_map:
        return host_map[normalized]

    # Allow bare "localhost" / "127.0.0.1" to fall through to default
    return default_customer_id
