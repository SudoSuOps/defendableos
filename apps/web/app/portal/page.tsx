"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Card, Stat } from "@/components/ui/Card";
import { api } from "@/lib/api";

interface AssetSummary {
  id: string;
  public_asset_reference: string;
  name: string;
  status: string;
  created_at: string;
}

interface Health {
  integrations: { brave_configured: boolean; kimi_configured: boolean; ens_mode: string };
}

export default function PortalDashboard() {
  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    api<AssetSummary[]>("/api/v1/assets").then(setAssets).catch(() => setAssets([]));
    api<Health>("/healthz").then(setHealth).catch(() => setHealth(null));
  }, []);

  return (
    <div className="max-w-7xl mx-auto w-full px-6 py-10">
      <div className="flex items-baseline justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">Portal</div>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-100">Dashboard</h1>
          <p className="text-sm text-stone-400 mt-1.5">
            Evidence first. Opinion second. Proof after review.
          </p>
        </div>
        <Link
          href="/portal/assets/new"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] text-sm font-semibold"
        >
          + Create Asset
        </Link>
      </div>

      <div className="mt-8 grid grid-cols-2 lg:grid-cols-6 gap-3">
        <Stat label="Active assets" value={assets.length} />
        <Stat label="Evidence packets" value="—" hint="per-asset" />
        <Stat label="Research sessions" value="—" hint="per-asset" />
        <Stat label="Validator flags" value="—" />
        <Stat label="Deeds ready" value="—" />
        <Stat label="Edge boxes" value={1} hint="demo seeded" />
      </div>

      <div className="mt-10 grid lg:grid-cols-[1.4fr_1fr] gap-6">
        <Card title="Assets" subtitle="Open one to start the Proof of Value pipeline.">
          {assets.length === 0 ? (
            <div className="text-sm text-stone-500">
              No assets yet. <Link href="/portal/assets/new" className="text-honey-300">Create one →</Link>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">
                <tr>
                  <th className="text-left py-2">Reference</th>
                  <th className="text-left py-2">Name</th>
                  <th className="text-left py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-900">
                {assets.map((a) => (
                  <tr key={a.id} className="hover:bg-stone-900/40">
                    <td className="py-3 font-mono text-stone-300">{a.public_asset_reference}</td>
                    <td className="py-3 text-stone-100">
                      <Link href={`/portal/assets/${a.id}`} className="hover:text-honey-300">{a.name}</Link>
                    </td>
                    <td className="py-3 text-stone-400">{a.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <Card title="Integrations" subtitle="Honest about what is live.">
          <ul className="text-sm space-y-3">
            <li className="flex justify-between">
              <span className="text-stone-300">Brave LLM Context</span>
              <span className={health?.integrations.brave_configured ? "text-emerald-300" : "text-stone-500"}>
                {health?.integrations.brave_configured ? "configured" : "not configured"}
              </span>
            </li>
            <li className="flex justify-between">
              <span className="text-stone-300">Kimi K2.6 gateway</span>
              <span className={health?.integrations.kimi_configured ? "text-emerald-300" : "text-stone-500"}>
                {health?.integrations.kimi_configured ? "configured" : "not configured"}
              </span>
            </li>
            <li className="flex justify-between">
              <span className="text-stone-300">ENS mode</span>
              <span className="font-mono text-stone-300">{health?.integrations.ens_mode ?? "mock"}</span>
            </li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
