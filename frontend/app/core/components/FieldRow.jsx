"use client";

/** Base FieldRow — shared form control used by base and customer LeadForms. */
export default function FieldRow({ field, values, setValues }) {
  return (
    <div className="field" style={field.style}>
      <label htmlFor={field.name} style={field.labelStyle}>
        {field.label}
        {field.customerSpecific ? (
          <em className="tag">customer-specific</em>
        ) : (
          <em className="tag muted">base</em>
        )}
      </label>
      {field.type === "checkbox" ? (
        <input
          id={field.name}
          type="checkbox"
          checked={Boolean(values[field.name])}
          onChange={(e) =>
            setValues((prev) => ({ ...prev, [field.name]: e.target.checked }))
          }
        />
      ) : field.type === "select" ? (
        <select
          id={field.name}
          value={values[field.name] ?? ""}
          onChange={(e) =>
            setValues((prev) => ({ ...prev, [field.name]: e.target.value }))
          }
        >
          {(field.options || []).map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ) : (
        <input
          id={field.name}
          type={field.type}
          required={field.required}
          value={values[field.name] ?? ""}
          onChange={(e) =>
            setValues((prev) => ({ ...prev, [field.name]: e.target.value }))
          }
        />
      )}
    </div>
  );
}
