/**
 * Base product lead form fields — shared by every customer.
 * Customer-specific fields are composed from customers/<id>/, not added here permanently.
 */

export const BASE_FIELDS = [
  {
    name: "name",
    label: "Name",
    type: "text",
    required: true,
    style: {
      background: "#3b82f6",
      padding: "0.65rem 0.75rem",
      borderRadius: "10px",
    },
  },
  { name: "email", label: "Email", type: "email", required: true },
  { name: "company", label: "Company", type: "text", required: false },
  { name: "address", label: "Address", type: "text", required: false },
];
