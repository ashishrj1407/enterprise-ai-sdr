"use client";

import { useEffect, useState } from "react";
import { listKnownCustomerIds } from "../core/resolveFrontend";
import { useResolvedFrontend } from "../core/hooks/useResolvedFrontend";

const CUSTOMERS = listKnownCustomerIds();
const STORAGE_KEY = "poc-active-customer";

function readStoredCustomer() {
  if (typeof window === "undefined") return "customer-1";
  return window.localStorage.getItem(STORAGE_KEY) || "customer-1";
}

/**
 * /info route
 * - Base customers → core/components/InfoPage.jsx
 * - customer-1 → customers/customer-1/components/InfoPage.jsx (override wins)
 */
export default function InfoRoutePage() {
  const [customerId, setCustomerId] = useState("customer-1");
  const resolved = useResolvedFrontend(customerId);

  useEffect(() => {
    setCustomerId(readStoredCustomer());
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, customerId);
    }
  }, [customerId]);

  if (!resolved) {
    return <main className="shell">Loading frontend…</main>;
  }

  const { config, theme, components } = resolved;
  const {
    AppShell,
    Hero,
    CustomerPanel,
    Styles,
    SiteNav,
    InfoPage,
    BrandIcon,
  } = components;

  return (
    <AppShell
      key={customerId}
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
    >
      <InfoPage
        config={config}
        accent={theme.accent}
        customerId={customerId}
        brandIcon={<BrandIcon />}
      />
    </AppShell>
  );
}
