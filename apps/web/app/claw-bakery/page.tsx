import type { Metadata } from "next";
import Link from "next/link";

import { Wordmark } from "@/components/brand/Wordmark";
import { PipelineRail } from "@/components/bakery/PipelineRail";
import { TribunalCards } from "@/components/bakery/TribunalCards";
import { SeededLanes } from "@/components/bakery/SeededLanes";
import { VaultTree } from "@/components/bakery/VaultTree";
import { Guardrails } from "@/components/bakery/Guardrails";
import { ProductLadder } from "@/components/bakery/ProductLadder";
import { PublicMetrics } from "@/components/bakery/PublicMetrics";
import { RoleStatusTable } from "@/components/bakery/RoleStatusTable";

export const metadata: Metadata = {
  title: "Claw Bakery · DefendableOS",
  description:
    "Receipt-backed AI agent inspection refinery · Honey/Jelly/Propolis Tribunal · pair candidates from real ClawCheck intakes. No agent approves its own Honey label. No deed issues without Validator review.",
  alternates: { canonical: "https://defendableos.com/claw-bakery" },
  openGraph: {
    title: "Claw Bakery · DefendableOS",
    description: "The 24/7 evidence + benchmark + pair + receipt refinery for AI workers. Inspect the agent. Grade the risk. Bake the proof.",
    url: "https://defendableos.com/claw-bakery",
    siteName: "DefendableOS",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Claw Bakery · DefendableOS",
    description: "Receipt-backed AI agent inspection refinery. Honey · Jelly · Propolis. No agent approves its own label.",
  },
  robots: { index: true, follow: true },
};

const START_CLAWCHECK_URL =
  process.env.NEXT_PUBLIC_DEFENDTHECLAW_URL ??
  "https://defendableos.com/defend-the-claw";

export default function ClawBakeryPage() {
  return (
    <main className="min-h-screen flex flex-col">
      <header className="px-6 py-5 border-b border-stone-900/80 flex items-center justify-between">
        <Link href="/" className="hover:opacity-90">
          <Wordmark />
        </Link>
        <nav className="hidden md:flex items-center gap-5 text-sm text-stone-400">
          <a href="https://defendableos.com" className="hover:text-stone-200">
            Public site
          </a>
          <a href="#pipeline" className="hover:text-stone-200">
            Pipeline
          </a>
          <a href="#lanes" className="hover:text-stone-200">
            Lanes
          </a>
          <a href="#vault" className="hover:text-stone-200">
            Vault
          </a>
          <a href="#guardrails" className="hover:text-stone-200">
            Guardrails
          </a>
          <Link
            href="/login"
            className="text-honey-300 font-semibold hover:text-honey-200"
          >
            Sign in
          </Link>
        </nav>
      </header>

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="px-6 pt-20 pb-16 lg:pt-28 lg:pb-24 max-w-6xl mx-auto w-full">
        <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">
          DefendableOS · Module
        </div>
        <h1 className="mt-4 text-4xl md:text-5xl lg:text-6xl font-semibold tracking-tight leading-[1.04]">
          Claw Bakery.
          <br />
          <span className="font-serif italic font-normal text-honey-300">
            Every claw inspected
          </span>{" "}
          strengthens the defense.
        </h1>
        <p className="mt-8 text-lg text-stone-300 max-w-3xl leading-relaxed">
          Claw Bakery is the DefendableOS evidence and benchmark refinery for
          AI workers. Every inspected agent can generate structured exposure
          records, validator-reviewed repair pairs, adversarial benchmark
          cases, and hashed receipts — without allowing an AI system to
          certify or train itself blindly.
        </p>
        <p className="mt-5 text-stone-400 max-w-3xl text-sm leading-relaxed">
          Inspect the agent. Grade the risk. Bake the proof.
        </p>

        <div className="mt-12 flex flex-wrap items-center gap-4">
          <a
            href={START_CLAWCHECK_URL}
            className="inline-flex items-center gap-2 px-5 py-3 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] font-semibold tracking-tight"
          >
            Start a ClawCheck →
          </a>
          <a
            href="#pipeline"
            className="inline-flex items-center gap-2 px-5 py-3 rounded border border-stone-700 text-stone-300 hover:border-stone-600 hover:text-stone-100 text-sm"
          >
            View how the bakery works
          </a>
        </div>

        <div className="mt-16">
          <PublicMetrics />
        </div>
      </section>

      {/* ── What enters the Bakery ───────────────────────────── */}
      <section className="px-6 py-16 border-t border-stone-900/80 bg-stone-950/40">
        <div className="max-w-6xl mx-auto w-full">
          <SectionLabel>What enters the Bakery</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            Four inputs · one refinery
          </h2>
          <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[
              {
                t: "Live Agent Intakes",
                d: "Real operator-described AI deployments captured through ClawCheck.",
              },
              {
                t: "Synthetic Forge Cases",
                d: "Controlled adversarial and edge-case scenarios produced for review.",
              },
              {
                t: "Validator Repairs",
                d: "Weak, generic, or incorrect findings rewritten into evidence-specific targets.",
              },
              {
                t: "Benchmark Receipts",
                d: "Passed, failed, denied, and remediated outcomes preserved with hashes.",
              },
            ].map((c) => (
              <div
                key={c.t}
                className="rounded-xl border border-stone-800 bg-stone-900/60 px-4 py-4"
              >
                <div className="text-stone-100 font-semibold tracking-tight">
                  {c.t}
                </div>
                <div className="mt-2 text-sm text-stone-400 leading-relaxed">
                  {c.d}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pipeline ─────────────────────────────────────────── */}
      <section id="pipeline" className="px-6 py-16 border-t border-stone-900/80">
        <div className="max-w-6xl mx-auto w-full">
          <SectionLabel>The Bakery Pipeline</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            From intake to specialist agent · with a Tribunal gate at every transition
          </h2>
          <div className="mt-8">
            <PipelineRail />
          </div>
        </div>
      </section>

      {/* ── Honey / Jelly / Propolis ────────────────────────── */}
      <section className="px-6 py-16 border-t border-stone-900/80 bg-stone-950/40">
        <div className="max-w-6xl mx-auto w-full">
          <SectionLabel>The Tribunal taxonomy</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            Honey · Jelly · Propolis
          </h2>
          <p className="mt-3 text-stone-400 max-w-3xl text-sm leading-relaxed">
            Every artifact that leaves the pipeline carries one of three
            labels. Honey is approved. Jelly is repairable. Propolis is
            preserved as adversarial evidence and never becomes a positive
            training target.
          </p>
          <div className="mt-8">
            <TribunalCards />
          </div>
        </div>
      </section>

      {/* ── Seeded lanes ────────────────────────────────────── */}
      <section id="lanes" className="px-6 py-16 border-t border-stone-900/80">
        <div className="max-w-6xl mx-auto w-full">
          <SectionLabel>Three live demonstration lanes</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            Computed by platform code · not by the model
          </h2>
          <p className="mt-3 text-stone-400 max-w-3xl text-sm leading-relaxed">
            Seeded fixtures · not real customer records. Each tier comes from
            the evidence-specific rule layer: SwarmScout matches{" "}
            <span className="font-mono text-stone-200">
              ELEVATED_BUSINESS_DATA_AND_DRAFTING_EXPOSURE
            </span>
            , RefundRanger matches{" "}
            <span className="font-mono text-stone-200">
              HIGH_FINANCIAL_AUTONOMOUS_ACTION
            </span>
            , RootClaw matches{" "}
            <span className="font-mono text-stone-200">
              HIGH_PRIVILEGED_OPERATIONS_COMPROMISE
            </span>
            . No agent approves its own tier.
          </p>
          <div className="mt-8">
            <SeededLanes />
          </div>
        </div>
      </section>

      {/* ── Vault ───────────────────────────────────────────── */}
      <section
        id="vault"
        className="px-6 py-16 border-t border-stone-900/80 bg-stone-950/40"
      >
        <div className="max-w-6xl mx-auto w-full grid gap-10 lg:grid-cols-[1fr_1.1fr]">
          <div>
            <SectionLabel>The evidence vault</SectionLabel>
            <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
              The Honey must survive every model generation.
            </h2>
            <p className="mt-4 text-stone-300 leading-relaxed">
              Models change. Agents change. Providers change. The value is in
              the verified operating record: the intake, the risk snapshot,
              the repair, the benchmark, the receipt, the manifest, and the
              deed history.
            </p>
            <p className="mt-4 text-stone-400 text-sm leading-relaxed">
              Claw Bakery preserves those records in a versioned evidence
              vault so DefendableOS can prove where each pair came from, what
              was approved, what failed, and what may be used for training.
            </p>
          </div>
          <VaultTree />
        </div>
      </section>

      {/* ── Guardrails ──────────────────────────────────────── */}
      <section id="guardrails" className="px-6 py-16 border-t border-stone-900/80">
        <div className="max-w-6xl mx-auto w-full">
          <SectionLabel>A bakery with a Tribunal gate</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            Eight rules the pipeline will never break
          </h2>
          <div className="mt-8">
            <Guardrails />
          </div>
        </div>
      </section>

      {/* ── Product ladder ──────────────────────────────────── */}
      <section className="px-6 py-16 border-t border-stone-900/80 bg-stone-950/40">
        <div className="max-w-6xl mx-auto w-full">
          <SectionLabel>The product ladder</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            Snapshot · Pro · Benchmark · Deed · Work Unit · Opinion
          </h2>
          <div className="mt-8">
            <ProductLadder />
          </div>
        </div>
      </section>

      {/* ── Kimi swarm role status (truthful) ────────────────── */}
      <section className="px-6 py-16 border-t border-stone-900/80 bg-stone-950/40">
        <div className="max-w-6xl mx-auto w-full">
          <SectionLabel>Role status · honest table</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            Six roles · one Kimi agent live · five scaffolded
          </h2>
          <div className="mt-8">
            <RoleStatusTable />
          </div>
        </div>
      </section>

      {/* ── ClawForge status (controlled preview) ───────────── */}
      <section className="px-6 py-16 border-t border-stone-900/80">
        <div className="max-w-6xl mx-auto w-full">
          <SectionLabel>ClawForge</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            Continuous adversarial case generation · Tribunal gated
          </h2>
          <div className="mt-6 rounded-xl border border-stone-800 bg-stone-900/60 px-5 py-5">
            <div className="flex flex-wrap items-center gap-3">
              <span className="inline-flex items-center px-2.5 py-1 rounded-full border border-amber-500/40 text-amber-300 bg-amber-500/[0.04] text-[9px] uppercase tracking-[0.16em] font-semibold">
                Disabled · controlled preview
              </span>
              <span className="text-xs text-stone-500">
                CLAW_BAKERY_CLAWFORGE_ENABLED=false by default
              </span>
            </div>
            <p className="mt-4 text-stone-300 text-sm leading-relaxed">
              ClawForge produces fictional AI-agent deployment cases,
              permission-edge scenarios, remediation challenges, and
              adversarial prompts for Validator and Tribunal review. Generated
              candidates ALWAYS land in{" "}
              <span className="font-mono text-stone-200">
                pair-candidates/pending/
              </span>{" "}
              with{" "}
              <span className="font-mono text-stone-200">synthetic=true</span>{" "}
              and{" "}
              <span className="font-mono text-stone-200">
                tribunal_label=PENDING
              </span>
              . ClawForge cannot issue deeds, cannot train models, and cannot
              promote a candidate to Honey on its own.
            </p>
          </div>
        </div>
      </section>

      {/* ── Final CTA ───────────────────────────────────────── */}
      <section className="px-6 py-20 border-t border-stone-900/80 bg-stone-950/80">
        <div className="max-w-4xl mx-auto w-full text-center">
          <div className="text-[10px] uppercase tracking-[0.32em] text-honey-400 font-semibold">
            Defend the claw
          </div>
          <h2 className="mt-5 text-3xl md:text-4xl font-semibold tracking-tight leading-tight">
            Before your agent touches files, customers, payments, credentials,
            infrastructure, or memory —{" "}
            <span className="font-serif italic text-honey-300">inspect it.</span>
          </h2>
          <div className="mt-10 flex items-center justify-center">
            <a
              href={START_CLAWCHECK_URL}
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded border border-honey-400/60 text-honey-100 hover:bg-honey-400/[0.1] font-semibold tracking-tight text-lg"
            >
              Start a ClawCheck →
            </a>
          </div>
          <p className="mt-6 text-stone-500 text-xs">
            Tribunal approval is required before training admission or deed
            issuance. No agent approves its own Honey label.
          </p>
        </div>
      </section>

      <footer className="px-6 py-6 border-t border-stone-900/80 text-xs text-stone-500">
        © 2026 Swarm and Bee LLC · DBA Swarm & Bee AI · D-U-N-S 138652395.
        DefendableOS™, Proof of Value™, Validate the Validator™, AIOV™,
        Defendable Deed™, ClawCheck™, AgentGrade™ and Claw Bakery™ are
        unregistered trademarks.
      </footer>
    </main>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">
      {children}
    </div>
  );
}
