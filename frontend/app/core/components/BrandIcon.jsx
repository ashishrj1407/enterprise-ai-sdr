"use client";

/**
 * BASE brand icon — used by customer-2 / customer-3 (and any customer without override).
 * Hexagon / platform mark.
 */
export default function BrandIcon({ title = "Base product icon" }) {
  return (
    <span className="brand-icon brand-icon-base" title={title} aria-label={title}>
      <svg viewBox="0 0 64 64" width="48" height="48" role="img">
        <defs>
          <linearGradient id="baseIconGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#334155" />
            <stop offset="100%" stopColor="#64748b" />
          </linearGradient>
        </defs>
        <polygon
          points="32,4 56,18 56,46 32,60 8,46 8,18"
          fill="url(#baseIconGrad)"
        />
        <circle cx="32" cy="32" r="10" fill="#f8fafc" />
        <rect x="28" y="22" width="8" height="20" rx="2" fill="#334155" />
      </svg>
    </span>
  );
}
