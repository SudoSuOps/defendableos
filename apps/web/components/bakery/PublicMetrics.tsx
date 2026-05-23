"use client";

import { useEffect, useState } from "react";

interface Metrics {
  intakes_captured: number;
  snapshots_generated: number;
  pending_pair_candidates: number;
  honey_pair_candidates: number;
  jelly_pair_candidates: number;
  jelly_repaired_to_honey: number;
  propolis_failures: number;
  receipts_hashed: number;
  dataset_releases: number;
  events_recorded: number;
  benchmark_lanes: string[];
  benchmark_runs_total?: number;
  propolis_denied_runs?: number;
  candidate_runs_pending_validator?: number;
  controlled_demonstration_label?: string;
}

function Stat({ label, value, hint }: { label: string; value: number | string; hint?: string }) {
  return (
    <div className="rounded-lg border border-stone-800 bg-stone-900/40 px-4 py-3">
      <div className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">{label}</div>
      <div className="text-stone-100 text-2xl font-semibold tracking-tight mt-1">{value}</div>
      {hint && <div className="text-xs text-stone-500 mt-1">{hint}</div>}
    </div>
  );
}

export function PublicMetrics() {
  const [m, setM] = useState<Metrics | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    fetch(`${base}/api/v1/claw-bakery/public-metrics`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => (d ? setM(d) : setError(true)))
      .catch(() => setError(true));
  }, []);

  if (error || !m) {
    return (
      <div>
        <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold mb-3">
          Demonstration lanes
        </div>
        <div className="rounded-lg border border-stone-800 bg-stone-900/40 px-5 py-4 text-sm text-stone-400">
          3 seeded agent-risk cases validated: <span className="text-stone-200">SwarmScout</span> ·{" "}
          <span className="text-stone-200">RefundRanger</span> ·{" "}
          <span className="text-stone-200">RootClaw</span>. Aggregate counters
          come online once the bakery backend is reachable.
        </div>
      </div>
    );
  }

  const showBatch = (m.benchmark_runs_total ?? 0) > 0;
  return (
    <div className="space-y-8">
      {showBatch && (
        <div className="rounded-xl border border-honey-400/40 bg-honey-400/[0.04] px-5 py-4">
          <div className="text-[10px] uppercase tracking-[0.22em] text-honey-300 font-semibold">
            Verified Demo Batch · Refund Agent v1
          </div>
          <div className="mt-3 grid gap-3 grid-cols-2 md:grid-cols-4">
            <Stat label="Controlled Tests Executed" value={m.benchmark_runs_total ?? 0} />
            <Stat
              label="Unsafe Agent Outcome"
              value={(m.propolis_denied_runs ?? 0) > 0 ? "DENIED / PROPOLIS" : "—"}
              hint="hard-fail conditions triggered"
            />
            <Stat
              label="Controlled Agent Outcome"
              value={(m.candidate_runs_pending_validator ?? 0) > 0 ? "Pending Validator Review" : "—"}
              hint="not yet a deed"
            />
            <Stat label="Receipts Generated" value={m.receipts_hashed} hint="SHA-256 immutable" />
          </div>
          <div className="mt-3 text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">
            No Deeds Issued · No Training Release Approved
          </div>
          <div className="mt-1 text-xs text-stone-400">
            {m.controlled_demonstration_label ??
              "Controlled Demonstration / Not Customer Production Evidence"}
          </div>
        </div>
      )}
      <div>
        <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold mb-3">
          Aggregate metrics (no private records exposed)
        </div>
        <div className="grid gap-3 grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          <Stat label="Intakes Captured" value={m.intakes_captured} />
          <Stat label="Snapshots Generated" value={m.snapshots_generated} />
          <Stat label="Benchmark Lanes" value={m.benchmark_lanes.length} hint={m.benchmark_lanes.join(" · ")} />
          <Stat
            label="Pair Candidates"
            value={
              m.pending_pair_candidates +
              m.honey_pair_candidates +
              m.jelly_pair_candidates +
              m.jelly_repaired_to_honey +
              m.propolis_failures
            }
            hint="pending + labeled"
          />
          <Stat label="Receipts Hashed" value={m.receipts_hashed} />
          <Stat label="Dataset Releases" value={m.dataset_releases} />
          <Stat label="Events Recorded" value={m.events_recorded} />
          <Stat label="PROPOLIS Failures" value={m.propolis_failures} hint="preserved as adversarial" />
        </div>
      </div>
    </div>
  );
}
