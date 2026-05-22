"use client";

import { useEffect, useState } from "react";

import { Card, Chip, Stat } from "@/components/ui/Card";
import { api } from "@/lib/api";

export default function AssetOverview({
  params,
}: {
  params: { assetId: string };
}) {
  const { assetId } = params;
  const [asset, setAsset] = useState<any>(null);
  const [manifest, setManifest] = useState<any>(null);
  const [evidenceCount, setEvidenceCount] = useState<number>(0);
  const [validator, setValidator] = useState<any>(null);
  const [latestDeed, setLatestDeed] = useState<any>(null);

  useEffect(() => {
    api(`/api/v1/assets/${assetId}`).then(setAsset).catch(() => {});
    api(`/api/v1/assets/${assetId}/manifest`).then(setManifest).catch(() => setManifest(null));
    api(`/api/v1/assets/${assetId}/evidence`).then((r: any) => setEvidenceCount(r.length)).catch(() => {});
    api(`/api/v1/assets/${assetId}/validator/latest`).then(setValidator).catch(() => setValidator(null));
    api(`/api/v1/assets/${assetId}/deeds`).then((r: any) => setLatestDeed(Array.isArray(r) && r.length ? r[0] : null)).catch(() => setLatestDeed(null));
  }, [assetId]);

  return (
    <div className="grid lg:grid-cols-[1.4fr_1fr] gap-6">
      <Card title="Compute identity" subtitle="Asset record · evidence stage">
        {asset?.compute_profile ? (
          <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <FieldDl label="Manufacturer" value={asset.compute_profile.manufacturer} />
            <FieldDl label="Model" value={asset.compute_profile.model} />
            <FieldDl label="GPU count" value={asset.compute_profile.gpu_count} />
            <FieldDl label="VRAM/GPU (GB)" value={asset.compute_profile.vram_per_gpu_gb} />
            <FieldDl label="CPU" value={asset.compute_profile.cpu} />
            <FieldDl label="RAM (GB)" value={asset.compute_profile.ram_gb} />
            <FieldDl label="OS" value={asset.compute_profile.operating_system} />
            <FieldDl label="Condition" value={asset.compute_profile.condition_status} />
            <FieldDl label="Intended use" value={asset.compute_profile.intended_use} />
            <FieldDl label="Operational" value={asset.compute_profile.operational_status} />
          </dl>
        ) : (
          <div className="text-sm text-stone-500">No compute profile attached.</div>
        )}
      </Card>

      <div className="space-y-4">
        <Card title="Workflow stage">
          <div className="grid grid-cols-2 gap-3">
            <Stat label="Evidence items" value={evidenceCount} />
            <Stat label="Manifest" value={manifest ? `v${manifest.version}` : "—"} />
            <Stat label="Validator" value={validator?.status ?? "—"} />
            <Stat
              label="Deed"
              value={latestDeed ? `v${latestDeed.version}` : "—"}
              hint={latestDeed?.is_public ? "published" : latestDeed ? "draft" : undefined}
            />
          </div>
        </Card>

        <Card title="Doctrine reminder">
          <p className="text-sm text-stone-300 leading-relaxed">
            Evidence first. Opinion second. <span className="text-honey-300 font-semibold">Proof</span> after review.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Chip tone="ok">PRIVATE BY DEFAULT</Chip>
            <Chip tone="pending">PRE-PUBLICATION</Chip>
          </div>
        </Card>
      </div>
    </div>
  );
}

function FieldDl({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <>
      <dt className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">{label}</dt>
      <dd className="text-stone-100">{value ?? "—"}</dd>
    </>
  );
}
