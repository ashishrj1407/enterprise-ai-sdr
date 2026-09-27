"""Customer-3 — configuration only; uses base product endpoint and schema.

Demonstrates that a customer can be onboarded with a manifest and dedicated
schema without adding custom Python routes.
"""

# No router — extension registry skips customers without a `router` attribute.
HOOKS: dict = {}
