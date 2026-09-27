"use client";

import { useEffect, useState } from "react";
import {
  listKnownCustomerIds,
  resolveFrontend,
} from "./core/resolveFrontend";

const CUSTOMERS = listKnownCustomerIds();
const STORAGE_KEY = "poc-active-customer";

function readStoredCustomer() {
  if (typeof window === "undefined") return "customer-1";
  return window.localStorage.getItem(STORAGE_KEY) || "customer-1";
}

/**
 * Inner tree remounts per customer so swapped hooks stay Rules-of-Hooks safe.
 */
function ResolvedApp({
  customerId,
  setCustomerId,
  resolved,
}) {
  const { config, theme, components, hooks } = resolved;
  const useLead = hooks.useLeadQualification;
  const lead = useLead(customerId, config);

  const {
    AppShell,
    Hero,
    CustomerPanel,
    LeadForm,
    LeadList,
    ArchitecturePanel,
    Styles,
    SiteNav,
    BrandIcon,
  } = components;

  return (
    <AppShell
      theme={theme}
      styles={<Styles />}
      siteNav={<SiteNav />}
      hero={<Hero accent={theme.accent} brandIcon={<BrandIcon />} />}
      customerPanel={
        <CustomerPanel
          customerId={customerId}
          setCustomerId={setCustomerId}
          customers={CUSTOMERS}
          config={config}
          accent={theme.accent}
        />
      }
      leadForm={
        <LeadForm
          config={config}
          values={lead.values}
          setValues={lead.setValues}
          accent={theme.accent}
          loading={lead.loading}
          error={lead.error}
          result={lead.result}
          onSubmit={lead.onSubmit}
        />
      }
      leadList={<LeadList leads={lead.leads} />}
      architecturePanel={<ArchitecturePanel />}
    />
  );
}

/**
 * Home route — Lead qualification (base form, customer overrides via slots).
 */
export default function HomePage() {
  const [customerId, setCustomerId] = useState("customer-1");
  const [resolved, setResolved] = useState(null);

  useEffect(() => {
    setCustomerId(readStoredCustomer());
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, customerId);
    }
  }, [customerId]);

  useEffect(() => {
    let cancelled = false;
    // Drop the previous package immediately so we never render customer-1
    // hooks/components under customer-2 (or vice versa) while resolve is in flight.
    setResolved(null);
    (async () => {
      const next = await resolveFrontend(customerId);
      if (!cancelled) setResolved(next);
    })();
    return () => {
      cancelled = true;
    };
  }, [customerId]);

  // Wait until resolved matches the active customer — otherwise a stale package
  // updates in place (same React tree) and swapping useLeadQualification
  // customer-1 ↔ base violates Rules of Hooks.
  if (!resolved || resolved.customerId !== customerId) {
    return <main className="shell">Loading frontend…</main>;
  }

  return (
    <ResolvedApp
      key={customerId}
      customerId={customerId}
      setCustomerId={setCustomerId}
      resolved={resolved}
    />
  );
}
