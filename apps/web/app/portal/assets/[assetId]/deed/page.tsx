"use client";

import { use, useEffect, useState } from "react";

import { Card, Chip } from "@/components/ui/Card";
import { api } from "@/lib/api";

interface Deed {
  id: string;
  deed_reference: string;
  version: number;
  status: string;
  is_public: boolean;
  public_slug: string | null;
  record_hash: string;
  deed_json: any;
  created_at: string;
}

export default function DeedPage({ params }: { params: Promise<{ assetId: string }> }) {
  const { assetId } = use(params);
  const [deeds, setDeeds] = useState<Deed[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function refresh() {
    const out = await api<Deed[]>(`/api/v1/assets/${assetId}/deeds`);
    setDeeds(out);
  }

  useEffect(() => { refresh(); }, [assetId]);

  async function createDeed() {
    setErr(null); setBusy(true);
    try {
      await api(`/api/v1/assets/${assetId}/deeds`, { method: "POST" });
      await refresh();
    } catch (e: any) {
      setErr(e?.message ?? "create failed");
    } finally { setBusy(false); }
  }

  async function publish(deedId: string) {
    setErr(null);
    try {
      await api(`/api/v1/deeds/${deedId}/publish`, { method: "POST", json: {} });
      await refresh();
    } catch (e: any) {
      setErr(e?.message ?? "publish failed");
    }
  }

  const latest = deeds[0];

  return (
    <div className="space-y-6">
      <Card
        title="Defendable Deed"
        subtitle="AIOV gives the opinion. DefendableOS proves the value."
        actions={
          <button
            onClick={createDeed}
            disabled={busy}
            className="px-4 py-2 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] text-sm font-semibold disabled:opacity-50"
          >
            {busy ? "Generating…" : "Generate deed version"}
          </button>
        }
      >
        {err && <div className="text-sm text-rose-400 mb-3">{err}</div>}
        {!latest ? (
          <div className="text-sm text-stone-500 py-8 text-center">
            No deed yet. Generate after the validator status reaches PASSED_FOR_PACKAGING.
          </div>
        ) : (
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Chip tone={latest.is_public ? "ok" : "pending"}>{latest.status}</Chip>
                <span className="text-xs text-stone-500">{latest.deed_reference}</span>
              </div>
              <DeedFieldRow label="Asset" value={latest.deed_json?.asset?.model} />
              <DeedFieldRow label="Manifest hash" value={latest.deed_json?.evidence_packet?.manifest_sha256} mono />
              <DeedFieldRow label="Validator receipt" value={latest.deed_json?.validator_review?.receipt_sha256} mono />
              <DeedFieldRow label="ENS identity (reserved)" value={latest.deed_json?.ens_identity?.name} mono />
              <DeedFieldRow label="Record hash" value={latest.record_hash} mono />
              {!latest.is_public ? (
                <button
                  onClick={() => publish(latest.id)}
                  className="mt-3 px-4 py-2 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] text-sm font-semibold"
                >
                  Publish public verification page
                </button>
              ) : (
                <a
                  href={`/verify/${latest.public_slug}`}
                  className="block mt-3 text-sm text-honey-300 hover:text-honey-200"
                >
                  Open public verification page →
                </a>
              )}
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold mb-2">deed.record.json</div>
              <pre className="text-[11.5px] font-mono text-stone-300 bg-stone-950 border border-stone-800 rounded p-3 overflow-x-auto max-h-[480px]">
{JSON.stringify(latest.deed_json, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </Card>

      {deeds.length > 1 && (
        <Card title="Version history">
          <ul className="text-sm divide-y divide-stone-900">
            {deeds.map((d) => (
              <li key={d.id} className="py-2.5 flex items-center justify-between">
                <span className="font-mono text-stone-300">{d.deed_reference}</span>
                <span className="text-stone-500">{d.status}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}

function DeedFieldRow({ label, value, mono }: { label: string; value: any; mono?: boolean }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">{label}</div>
      <div className={`mt-1 text-sm ${mono ? "font-mono text-xs text-stone-300 break-all" : "text-stone-100"}`}>
        {value ?? "—"}
      </div>
    </div>
  );
}
