/**
 * Customer-3 — base product only.
 * No fieldPlan extras/overrides → resolveCustomerConfig uses base fields as-is.
 */
const config = {
  customerId: "customer-3",
  displayName: "BaseCo (Customer C — base only)",
  endpoint: "/base-endpoint1",
  resultType: "string",
  accent: "#334155",
  blurb:
    "Customer-3 has no custom frontend or backend code. It uses the base lead form and /base-endpoint1, with data stored in schema_customer_3.",
  // No fieldPlan → inherits BASE_FIELDS from the loader defaults.
};

export default config;
export { config };
