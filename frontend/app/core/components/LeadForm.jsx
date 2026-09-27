"use client";

import FieldRow from "./FieldRow";

/** Composable field list — shared by base and customer forms. */
export function LeadFormFields({ fields, values, setValues }) {
  return (
    <>
      {(fields || []).map((field) => (
        <FieldRow
          key={field.name}
          field={field}
          values={values}
          setValues={setValues}
        />
      ))}
    </>
  );
}

/** Composable submit + result block. */
export function LeadFormFooter({
  accent,
  loading,
  error,
  result,
  endpoint,
}) {
  return (
    <>
      <button type="submit" disabled={loading} style={{ background: accent }}>
        {loading ? "Submitting…" : `POST ${endpoint}`}
      </button>
      {error ? <pre className="error">{error}</pre> : null}
      {result ? <pre className="result">{JSON.stringify(result, null, 2)}</pre> : null}
    </>
  );
}

/**
 * BASE Lead qualification form.
 * Complete default implementation; customers should compose LeadFormFields /
 * LeadFormFooter instead of copying this markup.
 */
export default function LeadForm({
  config,
  values,
  setValues,
  accent,
  loading,
  error,
  result,
  onSubmit,
}) {
  return (
    <form className="panel lead-form" onSubmit={onSubmit}>
      <div className="form-zone">
        <h2>Lead qualification</h2>
        <LeadFormFields
          fields={config.fields}
          values={values}
          setValues={setValues}
        />
        <LeadFormFooter
          accent={accent}
          loading={loading}
          error={error}
          result={result}
          endpoint={config.endpoint}
        />
      </div>
    </form>
  );
}
