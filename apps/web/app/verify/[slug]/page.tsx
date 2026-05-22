import Link from "next/link";

import { Wordmark } from "@/components/brand/Wordmark";

interface PublicRecord {
  public_slug: string;
  deed_reference: string;
  version: number;
  record_hash: string;
  issued_at: string | null;
  deed_public: any;
}

async function getRecord(slug: string): Promise<PublicRecord | null> {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  try {
    const resp = await fetch(`${base}/api/v1/public/verify/${slug}`, { cache: "no-store" });
    if (!resp.ok) return null;
    return (await resp.json()) as PublicRecord;
  } catch {
    return null;
  }
}

export default async function VerifyPage({ params }: { params: { slug: string } }) {
  const { slug } = params;
  const record = await getRecord(slug);

  return (
    <main className="min-h-screen">
      <header className="px-6 py-5 border-b border-stone-900/80 flex items-center justify-between">
        <Wordmark />
        <Link href="https://defendableos.com" className="text-sm text-stone-400 hover:text-stone-200">
          defendableos.com
        </Link>
      </header>

      <section className="max-w-4xl mx-auto px-6 py-16">
        <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">
          Public verification
        </div>
        <h1 className="mt-2 text-3xl md:text-4xl font-semibold tracking-tight text-stone-100">
          Proof of Value record
        </h1>

        {!record ? (
          <div className="mt-10 rounded-xl border border-stone-800 bg-stone-900/60 p-8 text-stone-400 text-sm">
            Public record not found.
          </div>
        ) : (
          <div className="mt-10 grid lg:grid-cols-2 gap-6">
            <div className="deed-card rounded-xl p-7 space-y-4">
              <Row label="Deed reference" value={record.deed_reference} mono />
              <Row label="Version" value={`v${record.version}`} />
              <Row label="Issued at" value={record.issued_at ?? "—"} />
              <Row
                label="Asset"
                value={`${record.deed_public?.asset?.manufacturer ?? ""} ${record.deed_public?.asset?.model ?? ""}`.trim() || "—"}
              />
              <Row label="Asset class" value={record.deed_public?.asset?.asset_class ?? "—"} />
              <Row label="Manifest hash" value={record.deed_public?.evidence_packet?.manifest_sha256 ?? "—"} mono />
              <Row label="Validator receipt" value={record.deed_public?.validator_review?.receipt_sha256 ?? "—"} mono />
              <Row label="Validator status" value={record.deed_public?.validator_review?.status ?? "—"} />
              <Row label="ENS identity" value={record.deed_public?.ens_identity?.name ?? "—"} mono />
              <Row label="ENS status" value={record.deed_public?.ens_identity?.status ?? "—"} />
              <Row label="Record hash" value={record.record_hash} mono />
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold mb-2">deed-public.json</div>
              <pre className="text-[11.5px] font-mono text-stone-300 bg-stone-950 border border-stone-800 rounded p-4 overflow-x-auto">
{JSON.stringify(record.deed_public, null, 2)}
              </pre>
              <a
                href={`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/v1/public/verify/${record.public_slug}.json`}
                className="block mt-3 text-xs text-honey-300 hover:text-honey-200"
              >
                Download JSON →
              </a>
            </div>
          </div>
        )}

        <p className="mt-12 text-xs text-stone-500 leading-relaxed max-w-2xl italic">
          DefendableOS records are evidence and analysis packages. Asset-specific
          professional, legal, regulatory, licensing, authentication, insurance, or
          appraisal requirements may still apply. This page exposes only approved
          non-sensitive fields.
        </p>
      </section>
    </main>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="grid grid-cols-[170px_1fr] gap-4 items-baseline border-b border-stone-800/70 pb-3">
      <span className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">{label}</span>
      <span className={mono ? "font-mono text-stone-300 text-xs break-all" : "text-stone-100"}>
        {value}
      </span>
    </div>
  );
}
