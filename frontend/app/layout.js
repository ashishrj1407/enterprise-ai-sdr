import "./core/styles/base.css";

export const metadata = {
  title: "Customer Architecture POC",
  description: "Demo of customer-specific folders over a shared AI SDR base product",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
