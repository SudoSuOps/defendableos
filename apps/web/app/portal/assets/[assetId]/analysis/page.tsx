"use client";

import { use, useEffect, useState } from "react";

import { Card, Chip } from "@/components/ui/Card";
import { api } from "@/lib/api";

interface Analysis {
  id: string;
  version: number;
  status: string;
  analysis_json: any;
  narrative: string | null;
  missing_evidence_json: { missing_evidence_types?: string[] } | null;
  created_at: string;
}

export default function AnalysisPage({ params }: { params: Promise<{ assetId: string }> }) {
  const { assetId } = use(params);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function refresh() {
    const out = await api<Analysis[]>(`/api/v1/assets/${assetId}/aiov`);
    setAnalyses(out);
  }

  useEffect(() => { refresh(); }, [assetId]);

  async function generate() {
    setErr(null);
    setBusy(true);
    try {
      await api(`/api/v1/assets/${assetId}/aiov/generate`, {
        method: "POST",
        json: {
          included_evidence_item_ids: null,
          included_research_source_ids: null,
          notes: "Generate AIOV draft from all current evidence + research sources.",
        },
      });
      await refresh();
    } catch (e: any) {
      setErr(e?.message ?? "generate failed");
    } finally {
      setBusy(false);
    }
  }

  const latest = analyses[0];

  return (
    <div className="grid lg:grid-cols-[1.4fr_1fr] gap-6">
      <Card
        title="AIOV draft"
        subtitle="AI-assisted opinion of value · evidence-backed · reviewable."
        actions={
          <button
            onClick={generate}
            disabled={busy}
            className="px-4 py-2 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] text-sm font-semibold disabled:opacity-50"
          >
            {busy ? "Generating…" : "Generate / regenerate"}
          </button>
        }
      >
        {err && <div className="text-sm text-rose-400 mb-3">{err}</div>}
        {latest ? (
          <div className="space-y-5">
            <div className="flex items-center gap-2">
              <Chip tone="pending">{latest.status}</Chip>
              <span className="text-xs text-stone-500">v{latest.version}</span>
            </div>
            {latest.narrative && (
              <p className="text-sm text-stone-300 leading-relaxed whitespace-pre-wrap">
                {latest.narrative}
              </p>
            )}
            <details className="text-sm">
              <summary className="cursor-pointer text-stone-400 hover:text-stone-200">
                Show structured JSON
              </summary>
              <pre className="mt-3 text-[11.5px] font-mono text-stone-300 bg-stone-950 border border-stone-800 rounded p-3 overflow-x-auto">
{JSON.stringify(latest.analysis_json, null, 2)}
              </pre>
            </details>
          </div>
        ) : (
          <div className="text-sm text-stone-500 py-8 text-center">
            No AIOV draft yet. Generate after uploading evidence and running research.
          </div>
        )}
      </Card>

      <div className="space-y-4">
        <Card title="Limitations · always disclosed">
          <ul className="text-sm text-stone-300 space-y-1.5 list-disc list-inside marker:text-stone-600">
            <li>AI-assisted draft only</li>
            <li>Not a licensed appraisal</li>
            <li>Not a warranty, certification, or authentication guarantee</li>
          </ul>
        </Card>

        {latest?.missing_evidence_json?.missing_evidence_types && (
          <Card title="Missing evidence" subtitle="Surface them honestly · the validator will check.">
            <div className="flex flex-wrap gap-2">
              {latest.missing_evidence_json.missing_evidence_types.map((m: string) => (
                <Chip key={m} tone="warn">{m}</Chip>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
