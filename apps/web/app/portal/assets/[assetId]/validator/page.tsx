"use client";

import { use, useEffect, useState } from "react";

import { Card, Chip } from "@/components/ui/Card";
import { api } from "@/lib/api";

interface Check {
  check: string;
  status: string;
  severity?: string | null;
  finding?: string | null;
}
interface Review {
  id: string;
  version: number;
  status: string;
  protocol: string;
  receipt_sha256: string;
  checks_json: Check[];
  findings_json: any[] | null;
  created_at: string;
}

const PASS_CHIP: Record<string, "ok" | "warn" | "pending" | "neutral"> = {
  PASS: "ok",
  PASS_WITH_FLAG: "pending",
  FAIL: "warn",
  SKIPPED: "neutral",
};

export default function ValidatorPage({ params }: { params: Promise<{ assetId: string }> }) {
  const { assetId } = use(params);
  const [review, setReview] = useState<Review | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api<Review | null>(`/api/v1/assets/${assetId}/validator/latest`).then(setReview).catch(() => setReview(null));
  }, [assetId]);

  async function run() {
    setErr(null);
    setBusy(true);
    try {
      const out = await api<Review>(`/api/v1/assets/${assetId}/validator/run`, { method: "POST" });
      setReview(out);
    } catch (e: any) {
      setErr(e?.message ?? "validator run failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid lg:grid-cols-[1.6fr_1fr] gap-6">
      <Card
        title="Validate the Validator"
        subtitle="An AI opinion is not proof until the evidence survives challenge."
        actions={
          <button
            onClick={run}
            disabled={busy}
            className="px-4 py-2 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] text-sm font-semibold disabled:opacity-50"
          >
            {busy ? "Running…" : "Run validator"}
          </button>
        }
      >
        {err && <div className="text-sm text-rose-400 mb-3">{err}</div>}
        {!review ? (
          <div className="text-sm text-stone-500 py-8 text-center">No validator review yet.</div>
        ) : (
          <>
            <div className="flex items-center gap-3 mb-5">
              <Chip tone={review.status === "PASSED_FOR_PACKAGING" ? "ok" : "warn"}>{review.status}</Chip>
              <span className="text-xs text-stone-500">v{review.version} · {review.protocol}</span>
            </div>
            <table className="w-full text-sm">
              <thead className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">
                <tr>
                  <th className="text-left py-2">Check</th>
                  <th className="text-left py-2">Status</th>
                  <th className="text-left py-2">Severity</th>
                  <th className="text-left py-2">Finding</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-900">
                {review.checks_json.map((c) => (
                  <tr key={c.check}>
                    <td className="py-2 font-mono text-xs text-stone-300">{c.check}</td>
                    <td className="py-2"><Chip tone={PASS_CHIP[c.status] ?? "neutral"}>{c.status}</Chip></td>
                    <td className="py-2 text-stone-400">{c.severity ?? "—"}</td>
                    <td className="py-2 text-stone-400">{c.finding ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </Card>

      <div className="space-y-4">
        <Card title="Receipt">
          {review ? (
            <div className="space-y-2 text-sm">
              <div className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">receipt_sha256</div>
              <div className="font-mono text-xs text-stone-300 break-all">{review.receipt_sha256}</div>
            </div>
          ) : (
            <div className="text-sm text-stone-500">No receipt yet.</div>
          )}
        </Card>
        <Card title="Next">
          <p className="text-sm text-stone-300">
            When status is <span className="font-mono">PASSED_FOR_PACKAGING</span>, head to the
            Deed tab to generate a versioned Defendable Deed.
          </p>
        </Card>
      </div>
    </div>
  );
}
