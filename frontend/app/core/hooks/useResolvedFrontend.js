"use client";

import { useEffect, useState } from "react";
import { resolveFrontend } from "../resolveFrontend";

/**
 * Shared loader for any route that needs resolved customer UI.
 */
export function useResolvedFrontend(customerId) {
  const [resolved, setResolved] = useState(null);

  useEffect(() => {
    let cancelled = false;
    // Clear stale package on switch so callers never mix customerId with
    // another customer's components/hooks while resolveFrontend is loading.
    setResolved(null);
    (async () => {
      const next = await resolveFrontend(customerId);
      if (!cancelled) setResolved(next);
    })();
    return () => {
      cancelled = true;
    };
  }, [customerId]);

  if (resolved && resolved.customerId !== customerId) {
    return null;
  }

  return resolved;
}
