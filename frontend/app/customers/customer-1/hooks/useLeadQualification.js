"use client";

import { useEffect } from "react";
import { useLeadQualification as useBaseLeadQualification } from "../../../core/hooks/useLeadQualification";

/**
 * Customer-1 hook override.
 *
 * Pattern: wrap the base hook (do not copy it), then add customer-only behaviour.
 * Preference: this wins over core/hooks/useLeadQualification for customer-1 only.
 *
 * Demo behaviour:
 * - Prefills solar-friendly defaults for roof/bill when empty
 * - Tags successful results with a customer-1 solar note
 */
export function useLeadQualification(customerId, config) {
  const base = useBaseLeadQualification(customerId, config);

  useEffect(() => {
    if (!config?.fields) return;
    base.setValues((prev) => {
      const next = { ...prev };
      let changed = false;
      if (next.roof_size_sqft === "" || next.roof_size_sqft === undefined) {
        next.roof_size_sqft = 500;
        changed = true;
      }
      if (next.monthly_energy_bill === "" || next.monthly_energy_bill === undefined) {
        next.monthly_energy_bill = 120;
        changed = true;
      }
      return changed ? next : prev;
    });
    // Only when customer/config identity changes — not on every keystroke.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerId, config]);

  const result =
    base.result && typeof base.result === "object"
      ? {
          ...base.result,
          customer_hook: "customer-1",
          solar_note:
            typeof base.result.result === "number"
              ? `GreenGrid hook: solar-fit score ${base.result.result}`
              : "GreenGrid hook active",
        }
      : base.result;

  return {
    ...base,
    result,
  };
}

export default useLeadQualification;
