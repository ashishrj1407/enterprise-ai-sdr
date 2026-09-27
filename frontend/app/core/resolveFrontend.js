/**
 * Frontend resolver — base-first with customer override + automatic fallback.
 *
 * Preference:
 *   customer package (config + components + hooks + styles)  >  base core
 *
 * Customer packages are registered in `customers/registry.js` (not here),
 * so onboarding a customer does not require editing core UI code.
 */

import AppShell from "./layouts/AppShell";
import { BASE_COMPONENTS } from "./components";
import { BASE_FIELDS } from "./baseFields";
import { resolveCustomerConfig } from "./composeFields";
import { resolveTheme, BASE_THEME } from "./theme";
import { useLeadQualification } from "./hooks/useLeadQualification";
import { CUSTOMER_PACKAGES } from "../customers/registry";

export const COMPONENT_SLOTS = [
  "AppShell",
  "Hero",
  "CustomerPanel",
  "LeadForm",
  "LeadList",
  "ArchitecturePanel",
  "FieldRow",
  "Styles",
  "InfoPage",
  "SiteNav",
  "BrandIcon",
];

export const HOOK_SLOTS = ["useLeadQualification"];

const BASE_DEFAULTS = {
  endpoint: "/base-endpoint1",
  resultType: "string",
  accent: BASE_THEME.accent,
  fields: BASE_FIELDS,
  blurb: "Base product form.",
};

const BASE_HOOKS = {
  useLeadQualification,
};

export function listKnownCustomerIds() {
  return Object.keys(CUSTOMER_PACKAGES);
}

async function resolveLoader(loader) {
  if (typeof loader !== "function") return null;
  const mod = await loader();
  return mod?.default ?? mod ?? null;
}

/**
 * Resolve effective frontend for a customer.
 * @returns {{ customerId, config, theme, components, hooks, source }}
 */
export async function resolveFrontend(customerId) {
  const baseComponents = {
    ...BASE_COMPONENTS,
    AppShell,
  };

  const emptySource = {
    config: "base",
    components: Object.fromEntries(COMPONENT_SLOTS.map((s) => [s, "base"])),
    hooks: Object.fromEntries(HOOK_SLOTS.map((s) => [s, "base"])),
  };

  const packageLoader = CUSTOMER_PACKAGES[customerId];
  if (!packageLoader) {
    return {
      customerId,
      config: {
        ...BASE_DEFAULTS,
        customerId,
        displayName: customerId,
        blurb: "Unknown customer — falling back to base product form.",
      },
      theme: resolveTheme(BASE_DEFAULTS),
      components: baseComponents,
      hooks: { ...BASE_HOOKS },
      source: emptySource,
    };
  }

  const customerPackage = await packageLoader();
  const rawConfig = customerPackage.default ?? customerPackage.config ?? {};
  const config = resolveCustomerConfig(
    { ...BASE_DEFAULTS, customerId, displayName: customerId },
    rawConfig
  );
  const theme = resolveTheme(config);

  const customerComponentLoaders = customerPackage.components || {};
  const components = { ...baseComponents };
  const source = {
    config: "customer",
    components: {},
    hooks: {},
  };

  for (const slot of COMPONENT_SLOTS) {
    const loader = customerComponentLoaders[slot];
    if (typeof loader === "function") {
      const resolved = await resolveLoader(loader);
      if (resolved) {
        components[slot] = resolved;
        source.components[slot] = "customer";
        continue;
      }
    }
    source.components[slot] = "base";
  }

  const customerHookLoaders = customerPackage.hooks || {};
  const hooks = { ...BASE_HOOKS };
  for (const slot of HOOK_SLOTS) {
    const loader = customerHookLoaders[slot];
    if (typeof loader === "function") {
      const mod = await loader();
      const resolved = mod?.[slot] ?? mod?.default ?? null;
      if (resolved) {
        hooks[slot] = resolved;
        source.hooks[slot] = "customer";
        continue;
      }
    }
    source.hooks[slot] = "base";
  }

  return { customerId, config, theme, components, hooks, source };
}
