/**
 * Compose base + customer frontend fields with a hard rule:
 * customer values always win over base/core values.
 *
 * Usage:
 *   composeFields(BASE_FIELDS)                         // base only
 *   composeFields(BASE_FIELDS, { extras: [...] })      // base + customer fields
 *   composeFields(BASE_FIELDS, {
 *     order: ["name", "custom_field", "email", ...],
 *     overrides: { name: { style: { background: "red" } } },
 *     extras: [{ name: "custom_field", ... }],
 *   })
 *
 * Override rules:
 * - Scalar props on a field: customer replaces base
 * - style / labelStyle objects: shallow-merged, customer keys win
 * - style: null | labelStyle: null: clears the base style entirely
 * - order: customer-controlled display order (base fields omitted from order are hidden)
 */

function mergeStyle(baseStyle, customerStyle) {
  if (customerStyle === null) return undefined;
  if (customerStyle === undefined) return baseStyle ? { ...baseStyle } : undefined;
  return { ...(baseStyle || {}), ...customerStyle };
}

export function mergeField(baseField, customerField) {
  if (!baseField) {
    return { ...customerField, customerSpecific: customerField.customerSpecific ?? true };
  }
  if (!customerField) {
    return { ...baseField };
  }

  const merged = {
    ...baseField,
    ...customerField,
    style: mergeStyle(baseField.style, customerField.style),
    labelStyle: mergeStyle(baseField.labelStyle, customerField.labelStyle),
  };

  // Drop style keys when cleared
  if (merged.style === undefined) delete merged.style;
  if (merged.labelStyle === undefined) delete merged.labelStyle;

  return merged;
}

/**
 * @param {Array<object>} baseFields
 * @param {{
 *   order?: string[],
 *   overrides?: Record<string, object>,
 *   extras?: Array<object>,
 * }} [customerPlan]
 */
export function composeFields(baseFields, customerPlan = {}) {
  const { order, overrides = {}, extras = [] } = customerPlan;

  const byName = new Map();
  for (const field of baseFields) {
    byName.set(field.name, { ...field });
  }
  for (const field of extras) {
    if (!field?.name) continue;
    const existing = byName.get(field.name);
    byName.set(field.name, mergeField(existing, field));
  }
  for (const [name, override] of Object.entries(overrides)) {
    const existing = byName.get(name);
    byName.set(name, mergeField(existing, { name, ...override }));
  }

  if (Array.isArray(order) && order.length > 0) {
    const ordered = [];
    const seen = new Set();
    for (const name of order) {
      const field = byName.get(name);
      if (!field) continue;
      ordered.push(field);
      seen.add(name);
    }
    // Append any extras not listed in order (keeps customer additions from being lost)
    for (const field of extras) {
      if (field?.name && !seen.has(field.name) && byName.has(field.name)) {
        ordered.push(byName.get(field.name));
        seen.add(field.name);
      }
    }
    return ordered;
  }

  // Default order: base fields, then extras not already in base
  const baseNames = new Set(baseFields.map((f) => f.name));
  const result = baseFields.map((f) => byName.get(f.name));
  for (const field of extras) {
    if (field?.name && !baseNames.has(field.name)) {
      result.push(byName.get(field.name));
    }
  }
  return result;
}

/**
 * Resolve a full customer UI config so top-level customer keys also win over defaults.
 */
export function resolveCustomerConfig(baseDefaults, customerConfig) {
  const plan = customerConfig.fieldPlan;
  const fields = plan
    ? composeFields(baseDefaults.fields || [], plan)
    : customerConfig.fields || baseDefaults.fields || [];

  return {
    ...baseDefaults,
    ...customerConfig,
    fields,
  };
}
