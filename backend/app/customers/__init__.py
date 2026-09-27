"""Customer package — manifests and auto-discovery only.

Core product code imports from here via the extension registry.
Customer-specific logic lives only under app/customers/<customer_id>/.
"""

from app.core.extension_registry import (
    discover_customers,
    get_customer_manifest,
    get_hook,
    invoke_hook,
    iter_customer_routers,
    list_customers,
)

__all__ = [
    "discover_customers",
    "get_customer_manifest",
    "get_hook",
    "invoke_hook",
    "iter_customer_routers",
    "list_customers",
]
