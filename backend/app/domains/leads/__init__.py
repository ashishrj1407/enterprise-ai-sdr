"""Base product lead domain — shared qualification logic (string result)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text

from app.core.database import tenant_session


class BaseLeadRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    company: str | None = Field(default=None, max_length=120)
    address: str | None = Field(default=None, max_length=255)


class BaseLeadResponse(BaseModel):
    customer_id: str
    result_type: str = "string"
    result: str
    source: str = "base"
    persisted: bool = False


def qualify_lead_base(customer_id: str, payload: BaseLeadRequest) -> BaseLeadResponse:
    """Base product behaviour: return a human-readable qualification string."""
    label = "qualified" if payload.company else "needs_review"
    result = f"{label}:{payload.name}"

    with tenant_session(customer_id) as db:
        db.execute(
            text(
                """
                INSERT INTO leads (name, email, company, address, result_type, result_value, source)
                VALUES (:name, :email, :company, :address, :result_type, :result_value, :source)
                """
            ),
            {
                "name": payload.name,
                "email": str(payload.email),
                "company": payload.company,
                "address": payload.address,
                "result_type": "string",
                "result_value": result,
                "source": "base",
            },
        )

    return BaseLeadResponse(
        customer_id=customer_id,
        result=result,
        persisted=True,
    )


def list_leads(customer_id: str, limit: int = 20) -> list[dict[str, Any]]:
    with tenant_session(customer_id) as db:
        rows = db.execute(
            text(
                """
                SELECT id, name, email, company, address, result_type, result_value, source, created_at
                FROM leads
                ORDER BY id DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings().all()
        results: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            created = item.get("created_at")
            if created is not None:
                item["created_at"] = created.isoformat()
            results.append(item)
        return results
