/**
 * Base product theme — inherited by every customer unless overridden.
 */
export const BASE_THEME = {
  accent: "#0f172a",
  pageStyle: undefined,
  pageClassName: "",
};

export function resolveTheme(customerConfig = {}) {
  return {
    accent: customerConfig.accent ?? BASE_THEME.accent,
    pageStyle: customerConfig.pageStyle ?? BASE_THEME.pageStyle,
    pageClassName: customerConfig.pageClassName ?? BASE_THEME.pageClassName,
  };
}
