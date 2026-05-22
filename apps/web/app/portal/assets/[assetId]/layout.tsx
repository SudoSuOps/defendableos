"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { Chip } from "@/components/ui/Card";
import { api } from "@/lib/api";

interface AssetOut {
  id: string;
  public_asset_reference: string;
  name: string;
  asset_class: string;
  category: string | null;
  status: string;
}

export default function AssetLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { assetId: string };
}) {
  const { assetId } = params;
  const pathname = usePathname();
  const [asset, setAsset] = useState<AssetOut | null>(null);

  useEffect(() => {
    api<AssetOut>(`/api/v1/assets/${assetId}`).then(setAsset).catch(() => setAsset(null));
  }, [assetId]);

  const base = `/portal/assets/${assetId}`;
  const tabs = [
    { href: base, label: "Overview" },
    { href: `${base}/evidence`, label: "Evidence" },
    { href: `${base}/research`, label: "AI Search" },
    { href: `${base}/analysis`, label: "AIOV" },
    { href: `${base}/validator`, label: "Validator" },
    { href: `${base}/deed`, label: "Deed" },
    { href: `${base}/audit`, label: "Audit" },
  ];

  return (
    <div className="max-w-7xl mx-auto w-full px-6 py-10">
      <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">Asset workspace</div>
      <div className="mt-2 flex items-baseline justify-between flex-wrap gap-3">
        <h1 className="text-3xl font-semibold tracking-tight text-stone-100">
          {asset?.name ?? "Loading…"}
        </h1>
        <div className="flex items-center gap-3 text-sm text-stone-400 font-mono">
          {asset && <span>{asset.public_asset_reference}</span>}
          {asset && <Chip tone="pending">{asset.status}</Chip>}
        </div>
      </div>

      <nav className="mt-6 border-b border-stone-900 flex flex-wrap gap-1">
        {tabs.map((t) => {
          const active = pathname === t.href || (t.href !== base && pathname.startsWith(t.href));
          const exactBase = t.href === base && pathname === base;
          const isActive = active || exactBase;
          return (
            <Link
              key={t.href}
              href={t.href}
              className={`px-3 py-2 text-sm border-b -mb-px ${
                isActive
                  ? "border-honey-400 text-stone-100"
                  : "border-transparent text-stone-400 hover:text-stone-200"
              }`}
            >
              {t.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-8">{children}</div>
    </div>
  );
}
