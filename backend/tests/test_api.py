"""API-level tests for base vs customer endpoints and isolation."""

import os

import pytest
from fastapi.testclient import TestClient

# Force a local sqlite-free path: tests that hit DB are skipped without MYSQL.
os.environ.setdefault(
    "DATABASE_URL",
    "mysql+pymysql://poc:pocpass@127.0.0.1:3306/generic?charset=utf8mb4",
)
os.environ["RUN_MIGRATIONS_ON_STARTUP"] = "false"
os.environ.setdefault("PLATFORM_DATABASE", "generic")

from app.core.extension_registry import discover_customers, list_customers
from app.main import create_app


@pytest.fixture(scope="module")
def client():
    discover_customers()
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_customers_discovered(client):
    discover_customers()
    ids = {c["customer_id"] for c in list_customers()}
    assert ids == {"customer-1", "customer-2", "customer-3"}


def test_me_resolves_customer_header(client):
    res = client.get("/api/me", headers={"X-Customer-Id": "customer-1"})
    assert res.status_code == 200
    body = res.json()
    assert body["customer_id"] == "customer-1"
    assert body["endpoint"] == "/customer-1-endpoint"
    assert body["result_type"] == "integer"
    assert "roof_size_sqft" in body["extra_fields"]


def test_me_customer_2(client):
    res = client.get("/api/me", headers={"X-Customer-Id": "customer-2"})
    assert res.status_code == 200
    body = res.json()
    assert body["endpoint"] == "/customer-2-endpoint"
    assert body["result_type"] == "percentage"


def test_me_customer_3_uses_base(client):
    res = client.get("/api/me", headers={"X-Customer-Id": "customer-3"})
    assert res.status_code == 200
    body = res.json()
    assert body["endpoint"] == "/base-endpoint1"
    assert body["result_type"] == "string"
    assert body["extra_fields"] == []


def test_customer_1_endpoint_forbidden_for_other_tenant(client):
    res = client.post(
        "/api/customer-1-endpoint",
        headers={"X-Customer-Id": "customer-2"},
        json={
            "name": "X",
            "email": "x@example.com",
            "roof_size_sqft": 100,
            "monthly_energy_bill": 50,
        },
    )
    assert res.status_code == 403


def test_customer_2_endpoint_forbidden_for_other_tenant(client):
    res = client.post(
        "/api/customer-2-endpoint",
        headers={"X-Customer-Id": "customer-1"},
        json={
            "name": "X",
            "email": "x@example.com",
            "consent_given": True,
            "product_type": "term_loan",
        },
    )
    assert res.status_code == 403
