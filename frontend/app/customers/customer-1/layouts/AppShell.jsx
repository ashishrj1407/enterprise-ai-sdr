"use client";

/**
 * Customer-1 AppShell layout override.
 *
 * Pattern: keep the same prop contract as base AppShell, change only layout chrome.
 * Preference: this wins over core/layouts/AppShell.jsx for customer-1 only.
 *
 * Demo behaviour:
 * - Adds a top "GreenGrid" ribbon
 * - Adds a footer note proving the layout slot was overridden
 * - Keeps all injected slots (nav, hero, form, …) intact
 */
export default function AppShell({
  theme,
  styles,
  siteNav,
  hero,
  customerPanel,
  children,
  leadForm,
  leadList,
  architecturePanel,
}) {
  const className = ["page", "app-shell-customer-1", theme.pageClassName]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className} style={theme.pageStyle}>
      {styles}
      <div className="customer-1-ribbon" role="banner">
        <strong>GreenGrid layout override</strong>
        <span>AppShell slot · customer-1 only</span>
      </div>
      <main className="shell">
        {siteNav}
        {hero}
        {customerPanel}
        {children}
        {(leadForm || leadList) && (
          <section className="grid">
            {leadForm}
            {leadList}
          </section>
        )}
        {architecturePanel}
        <footer className="customer-1-footer">
          Layout source:{" "}
          <code>customers/customer-1/layouts/AppShell.jsx</code>
        </footer>
      </main>
    </div>
  );
}
