"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/** Shared nav — part of base UI; works on every route. */
export default function SiteNav() {
  const pathname = usePathname();

  const links = [
    { href: "/", label: "Home (Lead form)" },
    { href: "/info", label: "Info page" },
  ];

  return (
    <nav className="site-nav panel">
      {links.map((link) => {
        const active = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            className={active ? "site-nav-link active" : "site-nav-link"}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
