"use client";

import { useEffect, useState } from "react";

import { Card, Chip } from "@/components/ui/Card";
import { api } from "@/lib/api";

const EVIDENCE_TYPES = [
  "PURCHASE_RECEIPT",
  "PRODUCT_SPECIFICATION",
  "SERIAL_OR_PHOTO",
  "NVIDIA_SMI_CAPTURE",
  "BENCHMARK_OUTPUT",
  "THERMAL_POWER_OUTPUT",
  "SYSTEM_SPECIFICATION",
  "MAINTENANCE_RECORD",
  "PRIOR_LISTING",
  "OTHER",
];

interface EvidenceItem {
  id: string;
  filename: string;
  evidence_type: string;
  visibility: string;
  ingestion_status: string;
  sha256_hash: string | null;
  byte_size: number;
  content_type: string | null;
  provenance: string | null;
  created_at: string;
}

interface Manifest {
  id: string;
  version: number;
  manifest_sha256: string;
  status: string;
  item_count: number;
  created_at: string;
}

export default function EvidencePage({ params }: { params: { assetId: string } }) {
  const { assetId } = params;
  const [items, setItems] = useState<EvidenceItem[]>([]);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function refresh() {
    const [list, m] = await Promise.all([
      api<EvidenceItem[]>(`/api/v1/assets/${assetId}/evidence`),
      api<Manifest | null>(`/api/v1/assets/${assetId}/manifest`).catch(() => null),
    ]);
    setItems(list);
    setManifest(m);
  }

  useEffect(() => { refresh(); }, [assetId]);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    const form = e.currentTarget;
    const fd = new FormData(form);
    try {
      await api(`/api/v1/assets/${assetId}/evidence/upload`, { method: "POST", formData: fd });
      form.reset();
      await refresh();
    } catch (e: any) {
      setErr(e?.message ?? "upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function regen() {
    const m = await api<Manifest>(`/api/v1/assets/${assetId}/manifest/regenerate`, { method: "POST" });
    setManifest(m);
  }

  return (
    <div className="grid lg:grid-cols-[1.4fr_1fr] gap-6">
      <Card title="Evidence items" subtitle="Private by default · SHA-256 on every upload">
        {items.length === 0 ? (
          <div className="text-sm text-stone-500 py-6">No evidence uploaded yet.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">
              <tr>
                <th className="text-left py-2">Filename</th>
                <th className="text-left py-2">Type</th>
                <th className="text-left py-2">SHA-256</th>
                <th className="text-left py-2">Provenance</th>
                <th className="text-left py-2">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-900">
              {items.map((it) => (
                <tr key={it.id}>
                  <td className="py-2.5 text-stone-100">{it.filename}</td>
                  <td className="py-2.5 text-stone-400">{it.evidence_type}</td>
                  <td className="py-2.5 font-mono text-stone-400 text-xs">
                    {it.sha256_hash ? it.sha256_hash.slice(0, 16) + "…" : "—"}
                  </td>
                  <td className="py-2.5 text-stone-400">{it.provenance ?? "—"}</td>
                  <td className="py-2.5">{it.ingestion_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <div className="space-y-4">
        <Card title="Upload evidence" subtitle="Server-side hashing, manifest auto-regenerates.">
          <form onSubmit={onSubmit} className="space-y-3">
            <label className="block text-sm">
              <span className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">File</span>
              <input
                type="file"
                name="file"
                required
                className="mt-1 w-full text-sm text-stone-300"
              />
            </label>
            <label className="block text-sm">
              <span className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">Evidence type</span>
              <select
                name="evidence_type"
                className="mt-1 w-full px-3 py-2 rounded bg-stone-950 border border-stone-800 text-stone-100"
                defaultValue="OTHER"
              >
                {EVIDENCE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </label>
            {err && <div className="text-xs text-rose-400">{err}</div>}
            <button
              disabled={busy}
              className="w-full px-4 py-2.5 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] text-sm font-semibold disabled:opacity-50"
            >
              {busy ? "Uploading…" : "Upload"}
            </button>
          </form>
        </Card>

        <Card title="Evidence manifest" subtitle="SHA-256 of the manifest of SHA-256s.">
          {manifest ? (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-stone-500">Version</span><span className="text-stone-100">v{manifest.version}</span></div>
              <div className="flex justify-between"><span className="text-stone-500">Items</span><span className="text-stone-100">{manifest.item_count}</span></div>
              <div className="flex justify-between"><span className="text-stone-500">Status</span><Chip tone="ok">{manifest.status}</Chip></div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold mb-1">manifest_sha256</div>
                <div className="font-mono text-xs text-stone-300 break-all">{manifest.manifest_sha256}</div>
              </div>
            </div>
          ) : (
            <div className="text-sm text-stone-500">No manifest yet. Upload one evidence item to generate v1.</div>
          )}
          <button
            onClick={regen}
            className="mt-4 w-full px-4 py-2 rounded border border-stone-700 text-stone-300 hover:border-stone-600 text-xs font-semibold"
          >
            Regenerate manifest
          </button>
        </Card>
      </div>
    </div>
  );
}
