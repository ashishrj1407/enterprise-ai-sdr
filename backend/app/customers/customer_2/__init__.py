"""Customer-2 (FinTrust) — percentage compliance score. Isolated from base product."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text

from app.core.database import tenant_session
from app.core.tenant import TenantContext, get_tenant_context

router = APIRouter(tags=["customer-2"])


class Customer2LeadRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    company: str | None = None
    address: str | None = Field(default=None, max_length=255)
    consent_given: bool = Field(description="Customer-2 extra field")
    product_type: Literal["term_loan", "line_of_credit", "invoice_finance"] = "term_loan"


class Customer2LeadResponse(BaseModel):
    customer_id: str = "customer-2"
    result_type: str = "percentage"
    result: float
    source: str = "customer-2"
    disclaimer_id: str
    persisted: bool = True


def compute_compliance_percentage(payload: Customer2LeadRequest) -> tuple[float, str]:
    """Customer-2-only compliance scoring — lives only in this folder."""
    if not payload.consent_given:
        return 0.0, "DISCLAIMER-BLOCKED"

    base = {
        "term_loan": 72.5,
        "line_of_credit": 81.0,
        "invoice_finance": 66.0,
    }[payload.product_type]
    return base, "DISCLAIMER-FT-UK-v6"


def score_and_persist(payload: Customer2LeadRequest) -> Customer2LeadResponse:
    pct, disclaimer_id = compute_compliance_percentage(payload)
    with tenant_session("customer-2") as db:
        db.execute(
            text(
                """
                INSERT INTO leads (
                    name, email, company, address, consent_given, product_type,
                    result_type, result_value, source, disclaimer_id
                ) VALUES (
                    :name, :email, :company, :address, :consent_given, :product_type,
                    :result_type, :result_value, :source, :disclaimer_id
                )
                """
            ),
            {
                "name": payload.name,
                "email": str(payload.email),
                "company": payload.company,
                "address": payload.address,
                "consent_given": payload.consent_given,
                "product_type": payload.product_type,
                "result_type": "percentage",
                "result_value": str(pct),
                "source": "customer-2",
                "disclaimer_id": disclaimer_id,
            },
        )
    return Customer2LeadResponse(result=pct, disclaimer_id=disclaimer_id)


@router.post("/customer-2-endpoint", response_model=Customer2LeadResponse)
def customer_2_endpoint(
    payload: Customer2LeadRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> Customer2LeadResponse:
    if tenant.customer_id != "customer-2":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="customer-2-endpoint is only available for customer-2",
        )
    return score_and_persist(payload)


def before_qualify(payload: dict[str, Any]) -> None:
    return None


HOOKS = {"before_qualify": before_qualify}
