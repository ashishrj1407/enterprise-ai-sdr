/**
 * Customer-1 frontend customization — solar extra fields + custom endpoint.
 *
 * Uses fieldPlan so customer order/overrides always win over base fields.
 */
const config = {
  customerId: "customer-1",
  displayName: "GreenGrid Solar (Customer A)",
  endpoint: "/customer-1-endpoint",
  resultType: "integer",
  accent: "#eab308",
  pageStyle: { background: "#fef9c3" },
  pageClassName: "theme-customer-1",
  // Customer-1-only: split Lead qualification panel at Email.
  formSectionSplit: {
    atField: "email",
    aboveStyle: { background: "#fecaca" },
    belowStyle: { background: "#bbf7d0" },
  },
  blurb:
    "Customer-1 adds roof size and energy bill fields. The form posts to /customer-1-endpoint and receives an integer solar-fit score. Base product code is unchanged.",
  fieldPlan: {
    // Customer-controlled order (Roof size between Name and Email).
    order: [
      "name",
      "roof_size_sqft",
      "email",
      "company",
      "address",
      "monthly_energy_bill",
    ],
    // Customer wins over base Name blue — uses customer-1 yellow theme.
    overrides: {
      name: {
        style: {
          background: "#eab308",
          padding: "0.65rem 0.75rem",
          borderRadius: "10px",
        },
      },
    },
    extras: [
      {
        name: "roof_size_sqft",
        label: "Roof size (sq ft)",
        type: "number",
        required: true,
        customerSpecific: true,
        labelStyle: { justifyContent: "flex-end", width: "100%" },
      },
      {
        name: "monthly_energy_bill",
        label: "Monthly energy bill ($)",
        type: "number",
        required: true,
        customerSpecific: true,
      },
    ],
  },
};

export default config;
export { config };
