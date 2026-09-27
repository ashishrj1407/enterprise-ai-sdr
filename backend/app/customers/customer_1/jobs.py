"""Customer-1 job overrides — enrich tenant tick payload.

Preference: this module is discovered by base tasks via import path;
customer-2 / customer-3 have no jobs.py → base behaviour only.
"""


def enrich_status_sync(payload: dict) -> dict:
    return {
        **payload,
        "source": "customer-1",
        "solar_note": (
            f"GreenGrid status sync saw {payload.get('lead_count', 0)} leads"
        ),
    }
