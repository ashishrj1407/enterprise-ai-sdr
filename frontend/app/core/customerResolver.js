/**
 * Customer resolver (frontend) — mirrors AI-SDR backendResolver pattern.
 *
 * Demo selection order:
 * 1. Explicit customerId (UI switcher / query param)
 * 2. Host map (customer-1.localhost → customer-1)
 * 3. Default customer (customer-3 — base product only)
 */

export const HOST_CUSTOMER_MAP = {
  "customer-1.localhost": "customer-1",
  "customer-2.localhost": "customer-2",
  "customer-3.localhost": "customer-3",
};

export const DEFAULT_CUSTOMER = "customer-3";

export function normalizeHost(host) {
  let base = String(host || "")
    .replace(/:\d+$/, "")
    .toLowerCase();
  if (base.startsWith("www.")) {
    base = base.slice(4);
  }
  return base;
}

export function resolveCustomer({ explicitId, host, hostMap = HOST_CUSTOMER_MAP, defaultCustomer = DEFAULT_CUSTOMER }) {
  if (explicitId) {
    return String(explicitId).trim().toLowerCase();
  }
  const normalized = normalizeHost(host);
  return hostMap[normalized] ?? defaultCustomer;
}
