"use client";

import { useEffect, useState } from "react";

import { Card, Chip } from "@/components/ui/Card";
import { api } from "@/lib/api";

type Lane = "PRIVATE_EVIDENCE" | "PUBLIC_WEB";

interface Source {
  id: string;
  source_type: string;
  title: string | null;
  source_url: string | null;
  publisher_domain: string | null;
  retrieved_at: string | null;
  evidence_classification: string;
  content_excerpt: string | null;
}

interface Session {
  id: string;
  query: string;
  source_lane: string;
  provider: string | null;
  status: string;
  created_at: string;
  sources: Source[];
}

export default function ResearchPage({ params }: { params: { assetId: string } }) {
  const { assetId } = params;
  const [lane, setLane] = useState<Lane>("PRIVATE_EVIDENCE");
  const [query, setQuery] = useState("");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function refresh() {
    const list = await api<Session[]>(`/api/v1/assets/${assetId}/research/sessions`);
    setSessions(list);
  }

  useEffect(() => { refresh(); }, [assetId]);

  async function onRun(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      const path = lane === "PRIVATE_EVIDENCE"
        ? `/api/v1/assets/${assetId}/research/private`
        : `/api/v1/assets/${assetId}/research/public`;
      await api(path, { method: "POST", json: { query } });
      setQuery("");
      await refresh();
    } catch (e: any) {
      setErr(e?.message ?? "search failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid lg:grid-cols-[1fr_1.4fr] gap-6">
      <Card title="Search" subtitle="Private evidence (org-scoped) or public market via Brave.">
        <form onSubmit={onRun} className="space-y-3">
          <div className="flex gap-2">
            {(["PRIVATE_EVIDENCE", "PUBLIC_WEB"] as Lane[]).map((l) => (
              <button
                key={l}
                type="button"
                onClick={() => setLane(l)}
                className={`px-3 py-1.5 rounded text-xs font-semibold border ${
                  lane === l
                    ? "border-honey-400 text-honey-200 bg-honey-400/[0.08]"
                    : "border-stone-700 text-stone-400 hover:text-stone-200"
                }`}
              >
                {l === "PRIVATE_EVIDENCE" ? "Private Evidence" : "Public Market · Brave"}
              </button>
            ))}
          </div>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              lane === "PRIVATE_EVIDENCE"
                ? "Search uploaded evidence…"
                : "Find current market evidence for a used NVIDIA RTX PRO 6000 Blackwell GPU"
            }
            className="w-full px-3 py-2 rounded bg-stone-950 border border-stone-800 text-stone-100 outline-none focus:border-honey-400"
            required
          />
          {err && <div className="text-xs text-rose-400">{err}</div>}
          <button
            disabled={busy}
            className="w-full px-4 py-2.5 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] text-sm font-semibold disabled:opacity-50"
          >
            {busy ? "Searching…" : "Run search"}
          </button>
        </form>
        <p className="mt-5 text-xs text-stone-500 leading-relaxed">
          Public-source classification (LISTING_PRICE vs CONFIRMED_SALE_PRICE) is unset by default. The validator will flag any source left as <span className="font-mono">UNKNOWN</span>.
        </p>
      </Card>

      <Card title="Research sessions" subtitle="Each session captures sources, excerpts and retrieved time.">
        {sessions.length === 0 ? (
          <div className="text-sm text-stone-500 py-8 text-center">No research sessions yet.</div>
        ) : (
          <div className="space-y-5">
            {sessions.map((s) => (
              <div key={s.id} className="border border-stone-800 rounded-lg p-4">
                <div className="flex items-baseline justify-between flex-wrap gap-2">
                  <div className="text-sm text-stone-100 font-medium">{s.query}</div>
                  <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">
                    <span>{s.source_lane}</span>
                    <Chip tone={s.status === "COMPLETED" ? "ok" : "warn"}>{s.status}</Chip>
                  </div>
                </div>
                {s.sources.length === 0 ? (
                  <div className="text-xs text-stone-500 mt-3">
                    {s.source_lane === "PUBLIC_WEB"
                      ? "Provider returned no sources (or BRAVE_API_KEY not configured)."
                      : "No matching private evidence."}
                  </div>
                ) : (
                  <ul className="mt-3 space-y-3">
                    {s.sources.map((src) => (
                      <li key={src.id} className="text-sm">
                        <div className="flex items-baseline justify-between gap-3">
                          <span className="text-stone-100">{src.title ?? "—"}</span>
                          <span className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">
                            {src.evidence_classification}
                          </span>
                        </div>
                        {src.source_url && (
                          <a href={src.source_url} className="text-xs text-honey-300 hover:text-honey-200 break-all">
                            {src.source_url}
                          </a>
                        )}
                        {src.content_excerpt && (
                          <p className="text-xs text-stone-400 mt-1.5 leading-relaxed line-clamp-3">
                            {src.content_excerpt}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
