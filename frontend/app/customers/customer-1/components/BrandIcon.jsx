"use client";

/**
 * Customer-1 brand icon override — solar / sun mark for GreenGrid.
 * Wins over base BrandIcon for customer-1 only.
 */
export default function BrandIcon({ title = "Customer-1 solar icon" }) {
  return (
    <span className="brand-icon brand-icon-customer-1" title={title} aria-label={title}>
      <svg viewBox="0 0 64 64" width="48" height="48" role="img">
        <defs>
          <radialGradient id="c1SunGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#fde68a" />
            <stop offset="100%" stopColor="#eab308" />
          </radialGradient>
        </defs>
        <circle cx="32" cy="32" r="14" fill="url(#c1SunGrad)" />
        {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => (
          <rect
            key={deg}
            x="30"
            y="4"
            width="4"
            height="12"
            rx="2"
            fill="#ca8a04"
            transform={`rotate(${deg} 32 32)`}
          />
        ))}
      </svg>
    </span>
  );
}
