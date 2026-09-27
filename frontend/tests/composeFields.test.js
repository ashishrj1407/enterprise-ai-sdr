import { describe, expect, it } from "vitest";
import { composeFields, mergeField } from "../app/core/composeFields.js";

const BASE = [
  {
    name: "name",
    label: "Name",
    type: "text",
    style: { background: "#3b82f6", padding: "8px" },
  },
  { name: "email", label: "Email", type: "email" },
];

describe("mergeField — customer wins over base", () => {
  it("lets customer override base style keys", () => {
    const merged = mergeField(BASE[0], {
      name: "name",
      style: { background: "red" },
    });
    expect(merged.style.background).toBe("red");
    expect(merged.style.padding).toBe("8px"); // untouched base key kept
    expect(merged.label).toBe("Name");
  });

  it("lets customer clear base style with null", () => {
    const merged = mergeField(BASE[0], { name: "name", style: null });
    expect(merged.style).toBeUndefined();
  });

  it("marks unknown fields as customer-specific by default", () => {
    const merged = mergeField(undefined, {
      name: "roof_size_sqft",
      label: "Roof",
      type: "number",
    });
    expect(merged.customerSpecific).toBe(true);
  });
});

describe("composeFields", () => {
  it("uses customer order and inserts extras between base fields", () => {
    const fields = composeFields(BASE, {
      order: ["name", "roof_size_sqft", "email"],
      extras: [
        {
          name: "roof_size_sqft",
          label: "Roof size (sq ft)",
          type: "number",
          customerSpecific: true,
        },
      ],
    });
    expect(fields.map((f) => f.name)).toEqual(["name", "roof_size_sqft", "email"]);
  });

  it("applies customer overrides over base blue Name style", () => {
    const fields = composeFields(BASE, {
      overrides: {
        name: { style: { background: "#fef3c7" } },
      },
    });
    expect(fields[0].style.background).toBe("#fef3c7");
  });
});
