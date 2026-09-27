"use client";

import { useEffect, useMemo, useState } from "react";

export function initialValues(fields) {
  const values = {};
  for (const field of fields || []) {
    if (field.type === "checkbox") values[field.name] = false;
    else if (field.type === "select") values[field.name] = field.options?.[0]?.value ?? "";
    else if (field.type === "number") values[field.name] = "";
    else values[field.name] = "";
  }
  return values;
}

/** Base hook for lead form submit + recent leads fetch. */
export function useLeadQualification(customerId, config) {
  const [values, setValues] = useState({});
  const [result, setResult] = useState(null);
  const [leads, setLeads] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!config?.fields) return;
    setValues(initialValues(config.fields));
    setResult(null);
    setError("");
  }, [customerId, config]);

  useEffect(() => {
    if (!config) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/backend/leads`, {
          headers: { "X-Customer-Id": customerId },
        });
        if (!res.ok) return;
        const data = await res.json();
        if (!cancelled) setLeads(data.leads || []);
      } catch {
        /* demo remains usable without prior leads */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [customerId, config, result]);

  const payload = useMemo(() => {
    if (!config?.fields) return {};
    const body = {};
    for (const field of config.fields) {
      let value = values[field.name];
      if (field.type === "number" && value !== "") value = Number(value);
      if (field.type === "checkbox") value = Boolean(value);
      body[field.name] = value;
    }
    return body;
  }, [config, values]);

  async function onSubmit(event) {
    event.preventDefault();
    if (!config) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch(`/api/backend${config.endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Customer-Id": customerId,
        },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail ? JSON.stringify(data.detail) : res.statusText);
      }
      setResult(data);
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return {
    values,
    setValues,
    result,
    leads,
    error,
    loading,
    onSubmit,
  };
}
