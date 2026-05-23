import Link from "next/link";

import { Wordmark } from "@/components/brand/Wordmark";

export default function Landing() {
  return (
    <main className="min-h-screen flex flex-col">
      <header className="px-6 py-5 border-b border-stone-900/80 flex items-center justify-between">
        <Wordmark />
        <nav className="flex items-center gap-5 text-sm text-stone-400">
          <a href="https://defendableos.com" className="hover:text-stone-200">Public site</a>
          <Link href="/claw-bakery" className="hover:text-stone-200">Claw Bakery</Link>
          <Link href="/compute-claw" className="hover:text-stone-200">ComputeClaw</Link>
          <Link href="/login" className="text-honey-300 font-semibold hover:text-honey-200">Sign in</Link>
        </nav>
      </header>

      <section className="flex-1 max-w-5xl mx-auto w-full px-6 py-24 lg:py-32">
        <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">
          The Platform
        </div>
        <h1 className="mt-4 text-4xl md:text-5xl lg:text-6xl font-semibold tracking-tight leading-[1.05]">
          Evidence first. Opinion second.{" "}
          <span className="font-serif italic font-normal text-honey-300">Proof</span> after review.
        </h1>
        <p className="mt-8 text-lg text-stone-300 max-w-3xl leading-relaxed">
          DefendableOS is the platform behind <span className="font-mono text-stone-200">defendableos.com</span>.
          Sign in to manage compute assets, upload evidence, run AIOV analysis,
          challenge it with the Validate-the-Validator pipeline, and package
          versioned <span className="font-serif italic text-honey-200">Defendable Deeds</span>.
        </p>

        <div className="mt-12 flex flex-wrap items-center gap-4">
          <Link
            href="/login"
            className="inline-flex items-center gap-2 px-5 py-3 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] font-semibold tracking-tight"
          >
            Enter the portal →
          </Link>
          <Link
            href="/claw-bakery"
            className="inline-flex items-center gap-2 px-5 py-3 rounded border border-stone-700 text-stone-300 hover:border-stone-600 hover:text-stone-100 text-sm"
          >
            Visit the Claw Bakery
          </Link>
          <a
            href="https://defendableos.com"
            className="inline-flex items-center gap-2 px-5 py-3 rounded border border-stone-700 text-stone-300 hover:border-stone-600 hover:text-stone-100 text-sm"
          >
            Read the doctrine
          </a>
        </div>

        <div className="mt-20 grid sm:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          {[
            ["Evidence", "Hashed. Manifested. Private."],
            ["AIOV", "AI Opinion of Value · always reviewable."],
            ["Validator", "Validate the Validator · receipted."],
            ["Deed", "Versioned · ENS-anchored · public-safe."],
          ].map(([t, s]) => (
            <div key={t} className="rounded-xl border border-stone-800 bg-stone-900/50 px-4 py-4">
              <div className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">{t}</div>
              <div className="text-stone-200 mt-1.5">{s}</div>
            </div>
          ))}
        </div>
      </section>

      <footer className="px-6 py-6 border-t border-stone-900/80 text-xs text-stone-500">
        © 2026 Swarm and Bee LLC · DBA Swarm & Bee AI · D-U-N-S 138652395.
        DefendableOS™, Proof of Value™, Validate the Validator™, AIOV™ and
        Defendable Deed™ are unregistered trademarks.
      </footer>
    </main>
  );
}
