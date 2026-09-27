import { describe, expect, it } from "vitest";
import {
  DEFAULT_CUSTOMER,
  normalizeHost,
  resolveCustomer,
} from "../app/core/customerResolver.js";

describe("customerResolver", () => {
  it("strips port and www", () => {
    expect(normalizeHost("www.customer-1.localhost:3000")).toBe("customer-1.localhost");
  });

  it("prefers explicit customer id", () => {
    expect(
      resolveCustomer({
        explicitId: "customer-2",
        host: "customer-1.localhost",
      })
    ).toBe("customer-2");
  });

  it("resolves from host map", () => {
    expect(
      resolveCustomer({
        explicitId: null,
        host: "customer-1.localhost",
      })
    ).toBe("customer-1");
  });

  it("falls back to default (base-only customer)", () => {
    expect(
      resolveCustomer({
        explicitId: null,
        host: "localhost",
      })
    ).toBe(DEFAULT_CUSTOMER);
  });
});
