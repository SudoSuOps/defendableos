"use client";

import { useState } from "react";

import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";

export default function EnrollPage() {
  const [token, setToken] = useState<string | null>(null);
  const [expires, setExpires] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function generate() {
    setErr(null); setBusy(true);
    try {
      const out = await api<{ token: string; expires_at: string; node_name_hint: string | null }>(
        "/api/v1/edge/enrollment-tokens",
        { method: "POST", json: { node_name_hint: "box-01" } },
      );
      setToken(out.token);
      setExpires(out.expires_at);
    } catch (e: any) {
      setErr(e?.message ?? "create failed");
    } finally { setBusy(false); }
  }

  return (
    <div className="max-w-3xl mx-auto w-full px-6 py-10">
      <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">Edge · Enroll</div>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-100">Enroll a Defendable Box</h1>
      <p className="text-sm text-stone-400 mt-1.5">Create a one-time token, then run the agent on the device.</p>

      <Card className="mt-8" title="Enrollment token" subtitle="Shown once · expires automatically.">
        {token ? (
          <div className="space-y-3">
            <div>
              <div className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">Token</div>
              <div className="mt-1 font-mono text-xs text-stone-200 bg-stone-950 border border-stone-800 rounded p-3 break-all">
                {token}
              </div>
            </div>
            <div className="text-xs text-stone-500">Expires {expires ? new Date(expires).toLocaleString() : "—"}</div>
            <pre className="text-[11.5px] font-mono text-stone-300 bg-stone-950 border border-stone-800 rounded p-3 overflow-x-auto">
{`defendable-box enroll \\
  --server ${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"} \\
  --token ${token} \\
  --node-name box-01`}
            </pre>
          </div>
        ) : (
          <div className="text-sm text-stone-500">No active token. Generate one to begin.</div>
        )}
        {err && <div className="text-sm text-rose-400 mt-3">{err}</div>}
        <button
          onClick={generate}
          disabled={busy}
          className="mt-5 px-4 py-2 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] text-sm font-semibold disabled:opacity-50"
        >
          {busy ? "Generating…" : "Generate enrollment token"}
        </button>
      </Card>
    </div>
  );
}
