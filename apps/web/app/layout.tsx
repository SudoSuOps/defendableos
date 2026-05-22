import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DefendableOS · Proof of Value",
  description:
    "The operating system for evidence-backed valuation. Validate the Validator. AIOV. Defendable Deeds.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <div aria-hidden className="fixed inset-0 pointer-events-none brand-grid" />
        <div className="relative z-10">{children}</div>
      </body>
    </html>
  );
}
