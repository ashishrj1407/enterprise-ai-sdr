"use client";

/**
 * BASE Info page content.
 * Used by all customers unless they override the InfoPage slot.
 */
export default function InfoPage({ config, accent, customerId, brandIcon }) {
  return (
    <section className="panel info-page">
      <div className="info-page-header">
        {brandIcon}
        <h2>Base Info Page</h2>
      </div>
      <p className="lede">
        This is the <strong>base</strong> HTML/UI page. Every customer inherits it
        unless they provide a customer-specific <code>InfoPage</code> override.
      </p>
      <div className="meta" style={{ borderLeftColor: accent }}>
        <strong>{config.displayName}</strong>
        <span>
          Active customer: <code>{customerId}</code>
        </span>
        <p>
          Icon source: base <code>BrandIcon</code> (slate platform mark)
        </p>
      </div>
    </section>
  );
}
