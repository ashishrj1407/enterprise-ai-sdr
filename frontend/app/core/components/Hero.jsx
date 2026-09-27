"use client";

/** Base hero banner. */
export default function Hero({ accent, brandIcon }) {
  return (
    <header className="hero" style={{ borderColor: accent }}>
      <div className="hero-top">
        {brandIcon}
        <div>
          <p className="eyebrow">Customer Architecture POC</p>
          <h1>One base product · isolated customer folders</h1>
        </div>
      </div>
      <p className="lede">
        Switch customers below. The base form stays the same; only the customer folder
        contributes extra fields and the target API endpoint.
      </p>
    </header>
  );
}
