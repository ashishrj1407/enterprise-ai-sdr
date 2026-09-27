"""Base product HTTP routes — shared by all customers unless overridden."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.extension_registry import invoke_hook
from app.core.tenant import TenantContext, get_tenant_context
from app.domains.leads import BaseLeadRequest, BaseLeadResponse, list_leads, qualify_lead_base

router = APIRouter(tags=["base"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/customers")
def customers() -> dict[str, Any]:
    from app.customers import list_customers

    return {"customers": list_customers()}


@router.get("/me")
def me(tenant: Annotated[TenantContext, Depends(get_tenant_context)]) -> dict[str, Any]:
    from app.customers import get_customer_manifest

    manifest = get_customer_manifest(tenant.customer_id) or {}
    return {
        "customer_id": tenant.customer_id,
        "display_name": tenant.display_name,
        "schema": tenant.schema_name,
        "endpoint": manifest.get("endpoint", "/base-endpoint1"),
        "extra_fields": manifest.get("extra_fields", []),
        "result_type": manifest.get("result_type", "string"),
    }


@router.post("/base-endpoint1", response_model=BaseLeadResponse)
def base_endpoint1(
    payload: BaseLeadRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> BaseLeadResponse:
    """
    Base product endpoint — returns a String qualification.

    Customer-3 uses this directly. Customers with a before_qualify hook can
    enrich behaviour without changing this handler's contract when they call
    their own endpoints instead.
    """
    # Optional extension point: if a customer registered a hook but still
    # hits the base route, we allow soft enrichment then fall back to core.
    hook_result = invoke_hook(
        tenant.customer_id,
        "before_qualify",
        payload.model_dump(),
    )
    if isinstance(hook_result, BaseLeadResponse):
        return hook_result

    return qualify_lead_base(tenant.customer_id, payload)


@router.get("/leads")
def get_leads(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> dict[str, Any]:
    return {
        "customer_id": tenant.customer_id,
        "schema": tenant.schema_name,
        "leads": list_leads(tenant.customer_id),
    }
