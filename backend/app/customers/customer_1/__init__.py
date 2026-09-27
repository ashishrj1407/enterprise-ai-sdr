"""Customer-1 (GreenGrid) — integer solar-fit score. Isolated from base product."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text

from app.core.database import tenant_session
from app.core.tenant import TenantContext, get_tenant_context

router = APIRouter(tags=["customer-1"])


class Customer1LeadRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    company: str | None = None
    address: str | None = Field(default=None, max_length=255)
    roof_size_sqft: int = Field(ge=0, description="Customer-1 extra field")
    monthly_energy_bill: float = Field(ge=0, description="Customer-1 extra field")


class Customer1LeadResponse(BaseModel):
    customer_id: str = "customer-1"
    result_type: str = "integer"
    result: int
    source: str = "customer-1"
    reason: str
    persisted: bool = True


def compute_solar_fit_score(payload: Customer1LeadRequest) -> tuple[int, str]:
    """Customer-1-only scoring — lives only in this folder."""
    size_pts = min(payload.roof_size_sqft // 50, 60)
    bill_pts = min(int(payload.monthly_energy_bill // 10), 40)
    score = size_pts + bill_pts
    reason = f"roof={size_pts}pts bill={bill_pts}pts"
    return score, reason


def score_and_persist(payload: Customer1LeadRequest) -> Customer1LeadResponse:
    score, reason = compute_solar_fit_score(payload)
    with tenant_session("customer-1") as db:
        db.execute(
            text(
                """
                INSERT INTO leads (
                    name, email, company, address, roof_size_sqft, monthly_energy_bill,
                    result_type, result_value, source
                ) VALUES (
                    :name, :email, :company, :address, :roof_size_sqft, :monthly_energy_bill,
                    :result_type, :result_value, :source
                )
                """
            ),
            {
                "name": payload.name,
                "email": str(payload.email),
                "company": payload.company,
                "address": payload.address,
                "roof_size_sqft": payload.roof_size_sqft,
                "monthly_energy_bill": payload.monthly_energy_bill,
                "result_type": "integer",
                "result_value": str(score),
                "source": "customer-1",
            },
        )
    return Customer1LeadResponse(result=score, reason=reason)


@router.post("/customer-1-endpoint", response_model=Customer1LeadResponse)
def customer_1_endpoint(
    payload: Customer1LeadRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> Customer1LeadResponse:
    if tenant.customer_id != "customer-1":
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="customer-1-endpoint is only available for customer-1",
        )
    return score_and_persist(payload)


def before_qualify(payload: dict[str, Any]) -> None:
    """Hook placeholder — customer-1 uses its dedicated endpoint instead."""
    return None


HOOKS = {"before_qualify": before_qualify}
