"use client";

/** Base customer switcher + metadata panel. */
export default function CustomerPanel({
  customerId,
  setCustomerId,
  customers,
  config,
  accent,
}) {
  return (
    <section className="panel">
      <label className="label" htmlFor="customer">
        Active customer
      </label>
      <select
        id="customer"
        value={customerId}
        onChange={(e) => setCustomerId(e.target.value)}
      >
        {customers.map((id) => (
          <option key={id} value={id}>
            {id}
          </option>
        ))}
      </select>

      <div className="meta" style={{ borderLeftColor: accent }}>
        <strong>{config.displayName}</strong>
        <span>
          Endpoint: <code>{config.endpoint}</code> · Result:{" "}
          <code>{config.resultType}</code>
        </span>
        <p>{config.blurb}</p>
      </div>
    </section>
  );
}
