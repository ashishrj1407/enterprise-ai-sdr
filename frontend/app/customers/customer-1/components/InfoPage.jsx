"use client";

/**
 * Customer-1 Info page override.
 * Takes precedence over base InfoPage for customer-1 only.
 */
export default function InfoPage({ config, accent, customerId, brandIcon }) {
  return (
    <section className="panel info-page info-page-customer-1">
      <div className="info-page-header">
        {brandIcon}
        <h2>Customer-1 Info Page</h2>
      </div>
      <p className="lede">
        This page is the <strong>customer-1</strong> override. Base customers
        (customer-2 / customer-3) still see the base Info page and base icon.
      </p>
      <div className="meta" style={{ borderLeftColor: accent }}>
        <strong>{config.displayName}</strong>
        <span>
          Active customer: <code>{customerId}</code>
        </span>
        <p>
          Icon source: customer-1 <code>BrandIcon</code> (yellow solar mark)
        </p>
      </div>
    </section>
  );
}
