"use client";

/** Base architecture explainer panel. */
export default function ArchitecturePanel() {
  return (
    <section className="panel architecture">
      <h2>How customization is isolated</h2>
      <ol>
        <li>
          <strong>Base product</strong> under <code>frontend/app/core/</code> owns the
          complete default UI (components, layout, hooks, theme, fields, styles).
        </li>
        <li>
          <strong>Customer packages</strong> under <code>frontend/app/customers/</code>{" "}
          override only what they need (components, styles, hooks, fieldPlan); missing
          pieces fall back to base. Register new customers in{" "}
          <code>customers/registry.js</code> only.
        </li>
        <li>
          Adding a fourth customer means a new folder + one registry line — not a fork
          of core UI.
        </li>
      </ol>
    </section>
  );
}
