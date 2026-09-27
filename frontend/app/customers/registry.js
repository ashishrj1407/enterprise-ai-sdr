/**
 * Customer package registry — the ONLY place to register a new customer package.
 *
 * Core (`resolveFrontend`) reads this file; it does not hard-code customer IDs.
 * Adding customer-4: create folder + one entry here. Do not edit core UI.
 */
export const CUSTOMER_PACKAGES = {
  "customer-1": () => import("./customer-1"),
  "customer-2": () => import("./customer-2"),
  "customer-3": () => import("./customer-3"),
};
