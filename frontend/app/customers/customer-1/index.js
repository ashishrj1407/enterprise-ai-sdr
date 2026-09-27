/**
 * Customer-1 package entry.
 * Exports config + optional component / style / hook overrides.
 * Unspecified slots automatically fall back to base.
 */
import config from "./config";

export default config;
export { config };

export const components = {
  // Layout override (AppShell slot)
  AppShell: () => import("./layouts/AppShell"),
  LeadForm: () => import("./components/LeadForm"),
  Styles: () => import("./components/Styles"),
  InfoPage: () => import("./components/InfoPage"),
  BrandIcon: () => import("./components/BrandIcon"),
};

/**
 * Behaviour overrides.
 * Example: useLeadQualification wraps the base hook and adds solar defaults + result note.
 */
export const hooks = {
  useLeadQualification: () => import("./hooks/useLeadQualification"),
};
