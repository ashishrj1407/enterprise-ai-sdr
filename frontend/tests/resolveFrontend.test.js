import { describe, expect, it } from "vitest";
import { resolveFrontend } from "../app/core/resolveFrontend.js";
import { CUSTOMER_PACKAGES } from "../app/customers/registry.js";

describe("resolveFrontend — base-first with customer override", () => {
  it("registers customers outside core", () => {
    expect(Object.keys(CUSTOMER_PACKAGES).sort()).toEqual([
      "customer-1",
      "customer-2",
      "customer-3",
    ]);
  });

  it("uses customer AppShell + hook + LeadForm/Styles/InfoPage/BrandIcon for customer-1", async () => {
    const resolved = await resolveFrontend("customer-1");
    expect(resolved.source.components.AppShell).toBe("customer");
    expect(resolved.source.components.LeadForm).toBe("customer");
    expect(resolved.source.components.Styles).toBe("customer");
    expect(resolved.source.components.InfoPage).toBe("customer");
    expect(resolved.source.components.BrandIcon).toBe("customer");
    expect(resolved.source.components.Hero).toBe("base");
    expect(resolved.source.hooks.useLeadQualification).toBe("customer");
    expect(resolved.config.fields.find((f) => f.name === "name").style.background).toBe(
      "#eab308"
    );
    expect(resolved.theme.pageClassName).toBe("theme-customer-1");
  });

  it("falls back entirely to base components/hooks for customer-2", async () => {
    const resolved = await resolveFrontend("customer-2");
    expect(resolved.source.components.LeadForm).toBe("base");
    expect(resolved.source.components.Styles).toBe("base");
    expect(resolved.source.components.InfoPage).toBe("base");
    expect(resolved.source.components.BrandIcon).toBe("base");
    expect(resolved.source.hooks.useLeadQualification).toBe("base");
    expect(resolved.config.fields.find((f) => f.name === "name").style.background).toBe(
      "#3b82f6"
    );
  });

  it("falls back to base for customer-3 (config-only package)", async () => {
    const resolved = await resolveFrontend("customer-3");
    expect(resolved.source.components.LeadForm).toBe("base");
    expect(resolved.source.components.Styles).toBe("base");
    expect(resolved.config.endpoint).toBe("/base-endpoint1");
  });
});
