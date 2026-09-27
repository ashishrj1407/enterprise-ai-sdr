/** Shared form helpers used by base and customer LeadForms. */

export function splitFieldsAround(fields, atField) {
  const list = fields || [];
  const index = list.findIndex((field) => field.name === atField);
  if (index < 0) {
    return { above: list, pivot: null, below: [] };
  }
  return {
    above: list.slice(0, index),
    pivot: list[index],
    below: list.slice(index + 1),
  };
}
