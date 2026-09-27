"use client";

import {
  LeadFormFields,
  LeadFormFooter,
} from "../../../core/components/LeadForm";
import { splitFieldsAround } from "../../../core/formUtils";

/**
 * Customer-1 LeadForm — composes base building blocks (no markup copy of base form).
 * Layout-only override: split zones around Email using formSectionSplit config.
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
  const splitConfig = config.formSectionSplit;
  const split = splitConfig
    ? splitFieldsAround(config.fields, splitConfig.atField)
    : null;

  if (!split || !splitConfig) {
    // Defer to the same base pieces in a single zone (still no duplicated FieldRow loop logic).
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

  return (
    <form className="panel lead-form customer-1-lead-form" onSubmit={onSubmit}>
      <div className="form-zone form-zone-above" style={splitConfig.aboveStyle}>
        <h2>Lead qualification</h2>
        <LeadFormFields
          fields={split.above}
          values={values}
          setValues={setValues}
        />
      </div>
      {split.pivot ? (
        <div className="form-zone form-zone-pivot">
          <LeadFormFields
            fields={[split.pivot]}
            values={values}
            setValues={setValues}
          />
        </div>
      ) : null}
      <div className="form-zone form-zone-below" style={splitConfig.belowStyle}>
        <LeadFormFields
          fields={split.below}
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
