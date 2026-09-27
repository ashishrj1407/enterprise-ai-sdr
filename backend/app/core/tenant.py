"""Immutable tenant context attached to every request (base product)."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.core.resolver import resolve_customer


@dataclass(frozen=True)
class TenantContext:
    customer_id: str
    display_name: str
    schema_name: str
    host: str


def get_tenant_context(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    x_customer_id: Annotated[str | None, Header(alias="X-Customer-Id")] = None,
) -> TenantContext:
    """Resolve tenant from X-Customer-Id header, then Host, then default."""
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    customer_id = resolve_customer(
        explicit_id=x_customer_id,
        host=host,
        host_map=settings.host_map(),
        default_customer_id=settings.default_customer_id,
    )

    from app.customers import get_customer_manifest

    manifest = get_customer_manifest(customer_id)
    if manifest is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown customer: {customer_id}",
        )

    return TenantContext(
        customer_id=customer_id,
        display_name=manifest["display_name"],
        schema_name=manifest["schema"],
        host=host,
    )
