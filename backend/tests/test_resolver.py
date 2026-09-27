"""Unit tests for customer resolver (no DB required)."""

from app.core.resolver import normalize_host, resolve_customer


def test_normalize_host_strips_port_and_www():
    assert normalize_host("www.Customer-1.localhost:3000") == "customer-1.localhost"


def test_resolve_prefers_explicit_header():
    result = resolve_customer(
        explicit_id="customer-2",
        host="customer-1.localhost",
        host_map={"customer-1.localhost": "customer-1"},
        default_customer_id="customer-3",
    )
    assert result == "customer-2"


def test_resolve_uses_host_map():
    result = resolve_customer(
        explicit_id=None,
        host="customer-1.localhost:8000",
        host_map={"customer-1.localhost": "customer-1"},
        default_customer_id="customer-3",
    )
    assert result == "customer-1"


def test_resolve_falls_back_to_default():
    result = resolve_customer(
        explicit_id=None,
        host="localhost",
        host_map={"customer-1.localhost": "customer-1"},
        default_customer_id="customer-3",
    )
    assert result == "customer-3"
