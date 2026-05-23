"use client";

import { useEffect, useState } from "react";

interface Fixture {
  agent_name: string;
  worker_kind: string;
  deployment_target: string;
  tier: string;
  rule_id: string;
  risk_class: string;
  deployment_status: string;
  deed_eligibility: string;
  reason: string;
  evidence_cited: string[];
  recommended_path: string[];
}

interface FixtureResponse {
  fixtures: Record<string, Fixture>;
  fixture_count: number;
}

const ORDER = ["swarmscout_v0_1", "refundranger_v0_1", "rootclaw_v0_1"];

const LANE_FOR_FIXTURE: Record<string, string> = {
  swarmscout_v0_1: "Business-agent intake and privacy-control evaluation.",
  refundranger_v0_1: "Financial autonomous-action adversarial pack.",
  rootclaw_v0_1: "Privileged operations and secret-leakage adversarial pack.",
};

function tierBadge(tier: string) {
  if (tier === "HIGH") return "border-rose-500/40 text-rose-300 bg-rose-500/[0.05]";
  if (tier === "ELEVATED") return "border-honey-400/40 text-honey-300 bg-honey-400/[0.05]";
  if (tier === "MODERATE") return "border-amber-500/40 text-amber-300 bg-amber-500/[0.05]";
  return "border-stone-700 text-stone-300 bg-stone-900/40";
}

export function SeededLanes({ initial }: { initial?: FixtureResponse }) {
  const [data, setData] = useState<FixtureResponse | null>(initial ?? null);
  useEffect(() => {
    if (initial) return;
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    fetch(`${base}/api/v1/claw-bakery/seeded-fixtures`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setData(d))
      .catch(() => undefined);
  }, [initial]);

  if (!data) {
    return (
      <div className="text-sm text-stone-400">
        Loading seeded demonstration fixtures…
      </div>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {ORDER.map((key) => {
        const fx = data.fixtures[key];
        if (!fx) return null;
        return (
          <div
            key={key}
            className="rounded-xl border border-stone-800 bg-stone-900/60 px-5 py-5 flex flex-col"
          >
            <div className="flex items-center justify-between gap-3">
              <div className="text-stone-100 font-semibold tracking-tight">
                {fx.agent_name}
              </div>
              <span
                className={`inline-flex items-center px-2.5 py-1 rounded-full border text-[9px] uppercase tracking-[0.16em] font-semibold ${tierBadge(
                  fx.tier
                )}`}
              >
                {fx.tier}
              </span>
            </div>
            <div className="mt-1 text-xs text-stone-500">
              {fx.worker_kind} · {fx.deployment_target}
            </div>
            <div className="mt-3 text-[10px] uppercase tracking-[0.18em] text-honey-400/80 font-semibold">
              Rule
            </div>
            <div className="text-stone-200 text-sm mt-1 font-mono">{fx.rule_id}</div>

            <div className="mt-3 text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">
              Why
            </div>
            <div className="text-stone-300 text-sm mt-1 leading-relaxed">
              {fx.reason}
            </div>

            <div className="mt-3 text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">
              Evidence cited
            </div>
            <ul className="text-xs text-stone-400 mt-1 list-disc list-inside space-y-0.5">
              {fx.evidence_cited.slice(0, 6).map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ul>

            <div className="mt-3 text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">
              Pair Lane
            </div>
            <div className="text-stone-300 text-sm mt-1">
              {LANE_FOR_FIXTURE[key]}
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2 text-[10px] uppercase tracking-[0.14em]">
              <div className="rounded border border-stone-800 bg-stone-950/50 px-2 py-2">
                <div className="text-stone-500 font-semibold">Status</div>
                <div className="text-stone-200 mt-0.5 normal-case tracking-normal text-xs">
                  {fx.deployment_status.replace(/_/g, " ")}
                </div>
              </div>
              <div className="rounded border border-stone-800 bg-stone-950/50 px-2 py-2">
                <div className="text-stone-500 font-semibold">Deed</div>
                <div className="text-stone-200 mt-0.5 normal-case tracking-normal text-xs">
                  {fx.deed_eligibility.replace(/_/g, " ")}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
