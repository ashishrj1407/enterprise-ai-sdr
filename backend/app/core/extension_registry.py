"""Extension registry — discovers customer folders without touching core routes.

New customers register by adding a folder under app/customers/<id>/ with a
manifest.json. Core code never hard-codes customer-specific endpoints.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter

CUSTOMERS_ROOT = Path(__file__).resolve().parent.parent / "customers"

_manifests: dict[str, dict[str, Any]] = {}
_routers: list[tuple[str, APIRouter]] = []
_hooks: dict[str, dict[str, Callable[..., Any]]] = {}


def _load_manifest(customer_dir: Path) -> dict[str, Any] | None:
    path = customer_dir / "manifest.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("customer_id", customer_dir.name.replace("_", "-"))
    return data


def discover_customers() -> None:
    """Scan app/customers/* and register manifests, routers, and hooks."""
    _manifests.clear()
    _routers.clear()
    _hooks.clear()

    if not CUSTOMERS_ROOT.exists():
        return

    for child in sorted(CUSTOMERS_ROOT.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if child.name == "__pycache__":
            continue

        manifest = _load_manifest(child)
        if not manifest:
            continue

        customer_id = manifest["customer_id"]
        _manifests[customer_id] = manifest

        module_name = f"app.customers.{child.name}"
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue

        router = getattr(module, "router", None)
        if router is not None:
            _routers.append((customer_id, router))

        hooks = getattr(module, "HOOKS", None)
        if isinstance(hooks, dict):
            _hooks[customer_id] = hooks


def get_customer_manifest(customer_id: str) -> dict[str, Any] | None:
    return _manifests.get(customer_id)


def list_customers() -> list[dict[str, Any]]:
    return sorted(_manifests.values(), key=lambda m: m["customer_id"])


def iter_customer_routers() -> list[tuple[str, APIRouter]]:
    return list(_routers)


def get_hook(customer_id: str, hook_name: str) -> Callable[..., Any] | None:
    return _hooks.get(customer_id, {}).get(hook_name)


def invoke_hook(customer_id: str, hook_name: str, payload: dict[str, Any]) -> Any | None:
    """Run a customer hook if registered; return None when absent (core fallback)."""
    hook = get_hook(customer_id, hook_name)
    if hook is None:
        return None
    return hook(payload)
