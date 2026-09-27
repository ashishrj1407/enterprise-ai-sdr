"use client";

/**
 * Base application shell / layout.
 * Customers may override AppShell; otherwise this default is used.
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
  const className = ["page", theme.pageClassName].filter(Boolean).join(" ");

  return (
    <div className={className} style={theme.pageStyle}>
      {styles}
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
      </main>
    </div>
  );
}
