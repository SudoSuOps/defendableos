"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";

interface AssetSummary {
  id: string;
  public_asset_reference: string;
  name: string;
  asset_class: string;
  category: string | null;
  status: string;
  created_at: string;
}

export default function AssetsPage() {
  const [assets, setAssets] = useState<AssetSummary[]>([]);

  useEffect(() => {
    api<AssetSummary[]>("/api/v1/assets").then(setAssets).catch(() => setAssets([]));
  }, []);

  return (
    <div className="max-w-7xl mx-auto w-full px-6 py-10">
      <div className="flex items-baseline justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">Assets</div>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-100">Asset inventory</h1>
        </div>
        <Link
          href="/portal/assets/new"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] text-sm font-semibold"
        >
          + Create Asset
        </Link>
      </div>

      <div className="mt-8">
        <Card>
          {assets.length === 0 ? (
            <div className="text-sm text-stone-500 py-10 text-center">
              No assets yet. The Proof of Value pipeline starts with one.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">
                <tr>
                  <th className="text-left py-2">Reference</th>
                  <th className="text-left py-2">Name</th>
                  <th className="text-left py-2">Class</th>
                  <th className="text-left py-2">Category</th>
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
                    <td className="py-3 text-stone-400">{a.asset_class}</td>
                    <td className="py-3 text-stone-400">{a.category ?? "—"}</td>
                    <td className="py-3 text-stone-400">{a.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </div>
  );
}
