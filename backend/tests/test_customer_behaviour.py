"""Tests for customer-specific scoring logic (pure functions, no DB)."""

from app.customers.customer_1 import Customer1LeadRequest, compute_solar_fit_score
from app.customers.customer_2 import Customer2LeadRequest, compute_compliance_percentage


def test_customer_1_returns_integer_score():
    payload = Customer1LeadRequest(
        name="Alex",
        email="alex@example.com",
        roof_size_sqft=500,  # 10 pts
        monthly_energy_bill=100,  # 10 pts
    )
    score, reason = compute_solar_fit_score(payload)
    assert isinstance(score, int)
    assert score == 20
    assert "roof=" in reason


def test_customer_1_caps_score_components():
    payload = Customer1LeadRequest(
        name="Big Roof",
        email="big@example.com",
        roof_size_sqft=10000,
        monthly_energy_bill=10000,
    )
    score, _ = compute_solar_fit_score(payload)
    assert score == 100


def test_customer_2_returns_percentage_with_consent():
    payload = Customer2LeadRequest(
        name="Blair",
        email="blair@example.com",
        consent_given=True,
        product_type="term_loan",
    )
    pct, disclaimer = compute_compliance_percentage(payload)
    assert isinstance(pct, float)
    assert pct == 72.5
    assert disclaimer.startswith("DISCLAIMER")


def test_customer_2_blocks_without_consent():
    payload = Customer2LeadRequest(
        name="No Consent",
        email="no@example.com",
        consent_given=False,
    )
    pct, disclaimer = compute_compliance_percentage(payload)
    assert pct == 0.0
    assert disclaimer == "DISCLAIMER-BLOCKED"


def test_customer_behaviours_are_isolated():
    """Customer-1 integer path and Customer-2 percentage path must not collide."""
    c1 = Customer1LeadRequest(
        name="A", email="a@example.com", roof_size_sqft=100, monthly_energy_bill=50
    )
    c2 = Customer2LeadRequest(
        name="B", email="b@example.com", consent_given=True, product_type="line_of_credit"
    )
    score, _ = compute_solar_fit_score(c1)
    pct, _ = compute_compliance_percentage(c2)
    assert isinstance(score, int)
    assert isinstance(pct, float)
    assert score != pct or type(score) is not type(pct)  # different result types
