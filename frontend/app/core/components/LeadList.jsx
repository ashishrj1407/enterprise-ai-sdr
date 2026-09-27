"use client";

/** Base recent-leads panel. */
export default function LeadList({ leads }) {
  return (
    <aside className="panel">
      <h2>Recent leads in tenant schema</h2>
      <p className="hint">
        Data is read from the active customer&apos;s MySQL schema only.
      </p>
      {leads.length === 0 ? (
        <p className="hint">No leads yet.</p>
      ) : (
        <ul className="leads">
          {leads.map((lead) => (
            <li key={lead.id}>
              <strong>{lead.name}</strong>
              <span>
                {lead.result_type}: {lead.result_value}
              </span>
              <small>{lead.source}</small>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
