/** Customer-2 frontend customization — consent fields + custom endpoint. */
const config = {
  customerId: "customer-2",
  displayName: "FinTrust Loans (Customer B)",
  endpoint: "/customer-2-endpoint",
  resultType: "percentage",
  accent: "#1d4ed8",
  blurb:
    "Customer-2 adds consent and product type. The form posts to /customer-2-endpoint and receives a compliance percentage. Base product code is unchanged.",
  fieldPlan: {
    extras: [
      {
        name: "consent_given",
        label: "Marketing consent given",
        type: "checkbox",
        required: true,
        customerSpecific: true,
      },
      {
        name: "product_type",
        label: "Product type",
        type: "select",
        required: true,
        customerSpecific: true,
        options: [
          { value: "term_loan", label: "Term loan" },
          { value: "line_of_credit", label: "Line of credit" },
          { value: "invoice_finance", label: "Invoice finance" },
        ],
      },
    ],
  },
};

export default config;
export { config };
