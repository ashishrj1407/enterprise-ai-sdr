/**
 * Backward-compatible config-only loader.
 * Prefer resolveFrontend() for full base+customer UI resolution.
 */
import { resolveFrontend, listKnownCustomerIds } from "./resolveFrontend";

export { listKnownCustomerIds };

export async function loadCustomerConfig(customerId) {
  const resolved = await resolveFrontend(customerId);
  return resolved.config;
}
