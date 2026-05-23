import Link from "next/link";

import { Wordmark } from "@/components/brand/Wordmark";

export const metadata = {
  title: "Claw Bakery · Admin · DefendableOS",
};

const ROWS = [
  {
    label: "Pair candidates · pending review",
    note: "list available via backend list_pair_candidates('pending') · gated behind admin auth",
  },
  {
    label: "Source attribution",
    note: "live_intake · synthetic_forge",
  },
  {
    label: "Risk class",
    note:
      "ELEVATED_BUSINESS_DATA_AND_DRAFTING_EXPOSURE · HIGH_FINANCIAL_AUTONOMOUS_ACTION · HIGH_PRIVILEGED_OPERATIONS_COMPROMISE",
  },
  {
    label: "Raw snapshot key",
    note: "raw-evidence/snapshots/<run_id>.json · immutable · separate from any redacted derivative",
  },
  {
    label: "Proposed Validator repair",
    note: "JELLY → repaired-target diff captured before relabel · stored under jelly-repaired/",
  },
  {
    label: "Consent status",
    note: "store_for_snapshot · allow_deidentified_training_use · allow_evaluation_use",
  },
  {
    label: "Redaction status",
    note: "PENDING → IN_PROGRESS → COMPLETED · residual PII raises RedactionRefusal",
  },
  {
    label: "Tribunal label actions",
    note: "HONEY · JELLY · JELLY_REPAIRED_TO_HONEY · PROPOLIS · QUARANTINED · PROPOLIS→HONEY refused",
  },
  {
    label: "Mark as evaluation candidate",
    note: "requires HONEY or JELLY_REPAIRED_TO_HONEY + validator PASSED + operator evaluation consent",
  },
  {
    label: "Mark as training candidate",
    note: "requires evaluation conditions + redaction COMPLETED + operator training consent",
  },
  {
    label: "Seal as holdout",
    note: "irreversible · sealed records can NEVER enter a training release",
  },
  {
    label: "Generate SHA-256 receipt",
    note: "wraps stored bytes · receipt itself stored immutably under receipts/sha256/",
  },
];

export default function AdminClawBakeryPage() {
  return (
    <main className="min-h-screen flex flex-col">
      <header className="px-6 py-5 border-b border-stone-900/80 flex items-center justify-between">
        <Link href="/" className="hover:opacity-90">
          <Wordmark />
        </Link>
        <nav className="flex items-center gap-5 text-sm text-stone-400">
          <Link href="/admin/deeds" className="hover:text-stone-200">
            Deeds
          </Link>
          <Link href="/admin/reviews" className="hover:text-stone-200">
            Reviews
          </Link>
          <Link href="/admin/ens" className="hover:text-stone-200">
            ENS
          </Link>
          <Link href="/admin/edge" className="hover:text-stone-200">
            Edge
          </Link>
        </nav>
      </header>

      <section className="max-w-5xl mx-auto w-full px-6 py-16">
        <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">
          Admin · placeholder
        </div>
        <h1 className="mt-3 text-3xl md:text-4xl font-semibold tracking-tight">
          Claw Bakery review dashboard
        </h1>
        <div className="mt-5 rounded-xl border border-amber-500/40 bg-amber-500/[0.04] px-5 py-4 text-sm text-amber-100 leading-relaxed">
          <strong className="text-amber-300">Auth gate required.</strong> The
          backend layer is live · pair candidates are written immutably,
          receipts are hashed, and events flow into the outbox. This page
          does not query private bakery records until the JWT admin gate is
          wired to the {" "}
          <span className="font-mono text-amber-200">
            /api/v1/claw-bakery/admin/*
          </span>{" "}
          endpoints. Until then, the routes return{" "}
          <span className="font-mono text-amber-200">501 Not Implemented</span>{" "}
          by design.
        </div>

        <div className="mt-10">
          <div className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">
            Review surface reservation
          </div>
          <ul className="mt-3 grid gap-3">
            {ROWS.map((r) => (
              <li
                key={r.label}
                className="rounded-lg border border-stone-800 bg-stone-900/40 px-4 py-3"
              >
                <div className="text-stone-100 font-semibold tracking-tight">
                  {r.label}
                </div>
                <div className="mt-1 text-xs text-stone-400 font-mono leading-relaxed">
                  {r.note}
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-12 rounded-xl border border-stone-800 bg-stone-900/60 px-5 py-5">
          <div className="text-stone-100 font-semibold tracking-tight">
            What the platform refuses to display here
          </div>
          <ul className="mt-3 text-sm text-stone-300 list-disc list-inside space-y-1.5">
            <li>Operator credentials or any access token, key, or .env value.</li>
            <li>
              Raw <span className="font-mono text-stone-200">operator_attested_context</span>{" "}
              · only redacted derivatives may be rendered.
            </li>
            <li>
              Customer-identifying fields · names, emails, addresses, phone
              numbers, payment instruments.
            </li>
            <li>
              Issued-deed evidence · those records flow through the
              Defendable Deed pipeline, not this dashboard.
            </li>
          </ul>
        </div>
      </section>

      <footer className="px-6 py-6 border-t border-stone-900/80 text-xs text-stone-500">
        © 2026 Swarm and Bee LLC · DBA Swarm & Bee AI · D-U-N-S 138652395.
      </footer>
    </main>
  );
}
