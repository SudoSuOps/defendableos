import type { Metadata } from "next";
import Link from "next/link";

import { Wordmark } from "@/components/brand/Wordmark";
import { CategoryCards } from "@/components/compute-claw/CategoryCards";
import { EvidenceStack } from "@/components/compute-claw/EvidenceStack";
import { ComputeClawProductLadder } from "@/components/compute-claw/ProductLadder";
import { SeededAssets } from "@/components/compute-claw/SeededAssets";

export const metadata: Metadata = {
  title: "ComputeClaw · DefendableOS",
  description:
    "Proof of Value Intake for AI-Capable Compute · Bring your GPU, server, edge box or AI workstation. ComputeClaw captures asset facts, gathers observed market evidence, prepares benchmark requirements and assembles the file for a Defendable Compute Proof Pack.",
};

export default function ComputeClawPage() {
  return (
    <main className="min-h-screen flex flex-col">
      <header className="px-6 py-5 border-b border-stone-900/80 flex items-center justify-between">
        <Link href="/" className="hover:opacity-90">
          <Wordmark />
        </Link>
        <nav className="hidden md:flex items-center gap-5 text-sm text-stone-400">
          <a href="https://defendableos.com" className="hover:text-stone-200">Public site</a>
          <Link href="/claw-bakery" className="hover:text-stone-200">Claw Bakery</Link>
          <a href="#evidence" className="hover:text-stone-200">Evidence Stack</a>
          <a href="#disclaimer" className="hover:text-stone-200">Asking-price disclaimer</a>
          <Link href="/login" className="text-honey-300 font-semibold hover:text-honey-200">Sign in</Link>
        </nav>
      </header>

      {/* ── Hero ──────────────────────────────────────────────── */}
      <section className="px-6 pt-20 pb-16 lg:pt-28 lg:pb-24 max-w-6xl mx-auto w-full">
        <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">
          DefendableOS · Compute Lane
        </div>
        <h1 className="mt-4 text-4xl md:text-5xl lg:text-6xl font-semibold tracking-tight leading-[1.04]">
          ComputeClaw.
          <br />
          <span className="font-serif italic font-normal text-honey-300">Proof of Value Intake</span>{" "}
          for AI-Capable Compute.
        </h1>
        <p className="mt-8 text-lg text-stone-300 max-w-3xl leading-relaxed">
          Bring your GPU, server, edge device or AI workstation. ComputeClaw
          captures asset facts, gathers observed market evidence, prepares
          benchmark requirements and assembles the file for a Defendable
          Compute Proof Pack.
        </p>
        <p className="mt-5 text-stone-400 max-w-3xl text-sm leading-relaxed">
          Observed asking prices are not verified paid transaction comps.
        </p>

        <div className="mt-12 flex flex-wrap items-center gap-4">
          <a
            href="#start-intake"
            className="inline-flex items-center gap-2 px-5 py-3 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] font-semibold tracking-tight"
          >
            Start Compute Intake →
          </a>
          <a
            href="#evidence"
            className="inline-flex items-center gap-2 px-5 py-3 rounded border border-stone-700 text-stone-300 hover:border-stone-600 hover:text-stone-100 text-sm"
          >
            See the Evidence Stack
          </a>
        </div>
      </section>

      {/* ── What ComputeClaw Can Review ──────────────────────── */}
      <section className="px-6 py-16 border-t border-stone-900/80 bg-stone-950/40">
        <div className="max-w-6xl mx-auto w-full">
          <SectionLabel>What ComputeClaw can review</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            From single GPU cards to GPU servers
          </h2>
          <div className="mt-8">
            <CategoryCards />
          </div>
        </div>
      </section>

      {/* ── Evidence Stack ───────────────────────────────────── */}
      <section id="evidence" className="px-6 py-16 border-t border-stone-900/80">
        <div className="max-w-6xl mx-auto w-full">
          <SectionLabel>The Evidence Stack</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            Intake · observe · benchmark · receipt · validator review
          </h2>
          <div className="mt-8">
            <EvidenceStack />
          </div>
        </div>
      </section>

      {/* ── Market Evidence Disclaimer ───────────────────────── */}
      <section id="disclaimer" className="px-6 py-16 border-t border-stone-900/80 bg-stone-950/40">
        <div className="max-w-4xl mx-auto w-full">
          <SectionLabel>Asking-price disclaimer</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            Observed market evidence is not a sold comp.
          </h2>
          <div className="mt-6 rounded-xl border border-honey-400/40 bg-honey-400/[0.04] px-5 py-5 text-stone-200 leading-relaxed">
            ComputeClaw may capture active eBay listing prices and market
            supply. <strong className="text-honey-300">These prices reflect
            seller asking positions at the time observed.</strong> They do
            not prove a completed sale, a paid transaction, equipment
            condition, or a final value conclusion.
          </div>
        </div>
      </section>

      {/* ── Why Benchmarking Matters ─────────────────────────── */}
      <section className="px-6 py-16 border-t border-stone-900/80">
        <div className="max-w-4xl mx-auto w-full">
          <SectionLabel>Why benchmarking matters</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            A listing tells you what a seller claims. A benchmark tells you what the machine does.
          </h2>
          <div className="mt-6 text-stone-300 leading-relaxed text-lg">
            A Defendable Proof Pack preserves both — separately and honestly.
          </div>
        </div>
      </section>

      {/* ── First Tracked Categories ─────────────────────────── */}
      <section className="px-6 py-16 border-t border-stone-900/80 bg-stone-950/40">
        <div className="max-w-6xl mx-auto w-full">
          <SectionLabel>First tracked categories</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            Workhorse · Premium Agent · Vintage Enterprise · Edge · Workstation · Infrastructure
          </h2>
          <p className="mt-3 text-stone-400 max-w-3xl text-sm leading-relaxed">
            6 category groups. Each tied to canonical SKUs ComputeClaw can
            normalize from observed market listings.
          </p>
        </div>
      </section>

      {/* ── How This Connects to the Claw Bakery ─────────────── */}
      <section className="px-6 py-16 border-t border-stone-900/80">
        <div className="max-w-4xl mx-auto w-full">
          <SectionLabel>How this connects to the Claw Bakery</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            Two claws · one evidence vault
          </h2>
          <div className="mt-6 text-stone-300 leading-relaxed">
            <p>
              <Link href="/claw-bakery" className="text-honey-300 underline hover:text-honey-200">
                Claw Bakery
              </Link>{" "}
              grades AI workers. ComputeClaw grades the evidence file around the
              compute those workers depend on.
            </p>
            <p className="mt-4 text-stone-400 text-sm">
              Agent capability + machine performance + observed market evidence +
              utility receipts = a stronger Proof of Value package.
            </p>
          </div>
        </div>
      </section>

      {/* ── Seeded Demo Assets ───────────────────────────────── */}
      <section className="px-6 py-16 border-t border-stone-900/80 bg-stone-950/40">
        <div className="max-w-6xl mx-auto w-full">
          <SectionLabel>Seeded demonstration assets</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            Three controlled demo intakes
          </h2>
          <p className="mt-3 text-stone-400 max-w-3xl text-sm leading-relaxed">
            Controlled Demonstration · Not Customer Production Evidence.
            No owner identity, fleet earnings or production data shown.
          </p>
          <div className="mt-8">
            <SeededAssets />
          </div>
        </div>
      </section>

      {/* ── Product Ladder ───────────────────────────────────── */}
      <section className="px-6 py-16 border-t border-stone-900/80">
        <div className="max-w-6xl mx-auto w-full">
          <SectionLabel>The product ladder</SectionLabel>
          <h2 className="mt-3 text-2xl md:text-3xl font-semibold tracking-tight">
            Snapshot · Market Pack · Benchmark · Proof Pack · Compute Deed
          </h2>
          <div className="mt-8">
            <ComputeClawProductLadder />
          </div>
        </div>
      </section>

      {/* ── Start Intake CTA ─────────────────────────────────── */}
      <section id="start-intake" className="px-6 py-20 border-t border-stone-900/80 bg-stone-950/80">
        <div className="max-w-4xl mx-auto w-full text-center">
          <div className="text-[10px] uppercase tracking-[0.32em] text-honey-400 font-semibold">
            Prove the box behind the claw
          </div>
          <h2 className="mt-5 text-3xl md:text-4xl font-semibold tracking-tight leading-tight">
            Before you sell, rent, insure or finance AI compute,{" "}
            <span className="font-serif italic text-honey-300">build a receipt-backed evidence file.</span>
          </h2>
          <div className="mt-10 flex items-center justify-center">
            <a
              href="https://defendableos.com/defend-the-claw"
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded border border-honey-400/60 text-honey-100 hover:bg-honey-400/[0.1] font-semibold tracking-tight text-lg"
            >
              Start Compute Intake →
            </a>
          </div>
          <p className="mt-6 text-stone-500 text-xs">
            No final value opinion. No deed issued without Validator review.
            Active listings are observed asking-price evidence only.
          </p>
        </div>
      </section>

      <footer className="px-6 py-6 border-t border-stone-900/80 text-xs text-stone-500">
        © 2026 Swarm and Bee LLC · DBA Swarm & Bee AI · D-U-N-S 138652395.
        DefendableOS™, Claw Bakery™, ComputeClaw™, Defendable Compute Proof Pack™
        and Defendable Deed™ are unregistered trademarks.
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
