"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

interface Catalogue {
  asset_types: string[];
  asset_categories: Record<string, string[]>;
  supported_outcomes: string[];
}

interface IntakeResponse {
  asset_intake_id: string;
  readiness_snapshot: {
    asset_intake_id: string;
    asset_summary: string;
    intended_outcome: string;
    evidence_supplied_summary: string;
    benchmark_status: string;
    observed_market_eligible: boolean;
    utility_evidence_status: string;
    readiness_status: string;
    recommended_next_steps: string[];
    doctrine_disclaimer: string;
  };
  bakery_envelope: {
    artifact_key: string;
    artifact_sha256: string;
    receipt_id: string;
  };
}

const PRETTY_OUTCOME: Record<string, string> = {
  sell: "Sell",
  insure: "Insure",
  finance: "Finance",
  document: "Document",
  rent: "Rent",
  benchmark: "Benchmark",
  prepare_proof_of_value_package: "Prepare Proof of Value Package",
};

export function IntakeForm() {
  const [catalogue, setCatalogue] = useState<Catalogue | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<IntakeResponse | null>(null);

  // Form state
  const [assetType, setAssetType] = useState("GPU");
  const [assetCategory, setAssetCategory] = useState("premium_agent_gpu");
  const [modelName, setModelName] = useState("");
  const [manufacturer, setManufacturer] = useState("NVIDIA");
  const [vramGb, setVramGb] = useState<string>("");
  const [quantity, setQuantity] = useState<number>(1);
  const [conditionClaimed, setConditionClaimed] = useState("Used / Operational");
  const [intendedOutcome, setIntendedOutcome] = useState("prepare_proof_of_value_package");
  const [useCase, setUseCase] = useState("AI inference, AI agent workloads");
  const [evPhotos, setEvPhotos] = useState(false);
  const [evSerial, setEvSerial] = useState(false);
  const [evBench, setEvBench] = useState(false);
  const [evPurchase, setEvPurchase] = useState(false);
  const [evRental, setEvRental] = useState(false);
  const [operatorNotes, setOperatorNotes] = useState("");
  const [consentDemo, setConsentDemo] = useState(false);
  const [attest, setAttest] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/compute-claw/categories`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setCatalogue(d))
      .catch(() => setError("Failed to load category catalogue. The intake form requires the API to be reachable."));
  }, []);

  // When category changes, reset model name to first option in that category
  useEffect(() => {
    if (catalogue && catalogue.asset_categories[assetCategory]?.length) {
      setModelName(catalogue.asset_categories[assetCategory][0]);
    }
  }, [catalogue, assetCategory]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    if (!attest) {
      setError("You must confirm asset_owner_attested before submitting.");
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        asset_owner_attested: true,
        asset_type: assetType,
        asset_category: assetCategory,
        manufacturer,
        model_name: modelName,
        vram_gb: vramGb ? parseInt(vramGb, 10) : null,
        quantity,
        condition_claimed: conditionClaimed,
        intended_outcome: intendedOutcome,
        use_case: useCase.split(",").map((s) => s.trim()).filter(Boolean),
        evidence_supplied: {
          photos: evPhotos,
          serial_hash: evSerial,
          benchmark_receipt: evBench,
          purchase_receipt: evPurchase,
          rental_receipts: evRental,
        },
        operator_notes: operatorNotes,
        consent: {
          store_for_review: true,
          allow_public_redacted_demo: consentDemo,
        },
      };
      const resp = await fetch(`${API_BASE}/api/v1/compute-claw/intake`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) {
        const j = await resp.json().catch(() => ({}));
        throw new Error(j.detail ?? `intake failed · HTTP ${resp.status}`);
      }
      const data: IntakeResponse = await resp.json();
      setResult(data);
    } catch (err) {
      setError(String(err instanceof Error ? err.message : err));
    } finally {
      setSubmitting(false);
    }
  }

  if (!catalogue && !error) {
    return (
      <div className="rounded-xl border border-stone-800 bg-stone-900/60 px-5 py-5 text-sm text-stone-400">
        Loading intake catalogue…
      </div>
    );
  }

  if (result) {
    const snap = result.readiness_snapshot;
    return (
      <div className="rounded-xl border border-honey-400/50 bg-honey-400/[0.05] px-6 py-6">
        <div className="text-[10px] uppercase tracking-[0.22em] text-honey-300 font-semibold">
          ComputeClaw readiness snapshot
        </div>
        <div className="mt-3 text-stone-100 font-semibold text-lg tracking-tight">
          {snap.asset_summary}
        </div>
        <div className="mt-1 text-xs text-stone-400 font-mono">{snap.asset_intake_id}</div>

        <dl className="mt-5 grid gap-3 sm:grid-cols-2 text-sm">
          <div className="rounded border border-stone-800 bg-stone-950/50 px-3 py-2">
            <dt className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">Requested outcome</dt>
            <dd className="text-stone-200 mt-1">{PRETTY_OUTCOME[snap.intended_outcome] ?? snap.intended_outcome}</dd>
          </div>
          <div className="rounded border border-stone-800 bg-stone-950/50 px-3 py-2">
            <dt className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">Evidence supplied</dt>
            <dd className="text-stone-200 mt-1">{snap.evidence_supplied_summary}</dd>
          </div>
          <div className="rounded border border-stone-800 bg-stone-950/50 px-3 py-2">
            <dt className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">Benchmark status</dt>
            <dd className="text-stone-200 mt-1">{snap.benchmark_status}</dd>
          </div>
          <div className="rounded border border-stone-800 bg-stone-950/50 px-3 py-2">
            <dt className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">Utility evidence</dt>
            <dd className="text-stone-200 mt-1">{snap.utility_evidence_status}</dd>
          </div>
          <div className="rounded border border-stone-800 bg-stone-950/50 px-3 py-2">
            <dt className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">Observed market rail</dt>
            <dd className="text-stone-200 mt-1">{snap.observed_market_eligible ? "Eligible for eBay Browse collection" : "Not eligible"}</dd>
          </div>
          <div className="rounded border border-stone-800 bg-stone-950/50 px-3 py-2">
            <dt className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">Readiness status</dt>
            <dd className="text-stone-200 mt-1 font-mono">{snap.readiness_status}</dd>
          </div>
        </dl>

        <div className="mt-5">
          <div className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold mb-2">
            Recommended next steps
          </div>
          <ol className="text-sm text-stone-300 list-decimal list-inside space-y-1">
            {snap.recommended_next_steps.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ol>
        </div>

        <div className="mt-5 text-xs text-stone-400 leading-relaxed border-l-2 border-honey-400/50 pl-3">
          {snap.doctrine_disclaimer}
        </div>

        <div className="mt-5 grid grid-cols-2 gap-2 text-[10px] uppercase tracking-[0.14em]">
          <div className="rounded border border-stone-800 bg-stone-950/50 px-2 py-2">
            <div className="text-stone-500 font-semibold">Receipt ID</div>
            <div className="text-stone-200 mt-0.5 normal-case tracking-normal text-xs font-mono">{result.bakery_envelope.receipt_id}</div>
          </div>
          <div className="rounded border border-stone-800 bg-stone-950/50 px-2 py-2">
            <div className="text-stone-500 font-semibold">Artifact sha256</div>
            <div className="text-stone-200 mt-0.5 normal-case tracking-normal text-[10px] font-mono break-all">{result.bakery_envelope.artifact_sha256.slice(0, 16)}…</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl border border-stone-800 bg-stone-900/60 px-6 py-6 space-y-5"
    >
      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Asset type">
          <select className="cc-select" value={assetType} onChange={(e) => setAssetType(e.target.value)}>
            {catalogue?.asset_types.map((t) => <option key={t}>{t}</option>)}
          </select>
        </Field>
        <Field label="Asset category">
          <select className="cc-select" value={assetCategory} onChange={(e) => setAssetCategory(e.target.value)}>
            {catalogue && Object.keys(catalogue.asset_categories).map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </Field>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Manufacturer">
          <input className="cc-input" value={manufacturer} onChange={(e) => setManufacturer(e.target.value)} required />
        </Field>
        <Field label="Model">
          <select className="cc-select" value={modelName} onChange={(e) => setModelName(e.target.value)}>
            {(catalogue?.asset_categories[assetCategory] ?? []).map((m) => <option key={m}>{m}</option>)}
          </select>
        </Field>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Field label="VRAM (GB, optional)">
          <input className="cc-input" type="number" min={0} max={4096} value={vramGb} onChange={(e) => setVramGb(e.target.value)} />
        </Field>
        <Field label="Quantity">
          <input className="cc-input" type="number" min={1} max={1000} value={quantity} onChange={(e) => setQuantity(parseInt(e.target.value || "1", 10))} required />
        </Field>
        <Field label="Condition claimed">
          <input className="cc-input" value={conditionClaimed} onChange={(e) => setConditionClaimed(e.target.value)} />
        </Field>
      </div>

      <Field label="Intended outcome">
        <select className="cc-select" value={intendedOutcome} onChange={(e) => setIntendedOutcome(e.target.value)}>
          {catalogue?.supported_outcomes.map((o) => <option key={o} value={o}>{PRETTY_OUTCOME[o] ?? o}</option>)}
        </select>
      </Field>

      <Field label="Use case (comma-separated)">
        <input className="cc-input" value={useCase} onChange={(e) => setUseCase(e.target.value)} placeholder="AI inference, GPU rental, training" />
      </Field>

      <fieldset className="rounded-lg border border-stone-800 bg-stone-950/40 px-4 py-3">
        <legend className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold px-2">Evidence supplied (so far)</legend>
        <div className="mt-2 grid gap-2 md:grid-cols-3 text-sm">
          <Check label="Photos" checked={evPhotos} onChange={setEvPhotos} />
          <Check label="Serial / identity hash" checked={evSerial} onChange={setEvSerial} />
          <Check label="Defendable benchmark receipt" checked={evBench} onChange={setEvBench} />
          <Check label="Purchase receipt" checked={evPurchase} onChange={setEvPurchase} />
          <Check label="Rental / income receipts" checked={evRental} onChange={setEvRental} />
        </div>
      </fieldset>

      <Field label="Operator notes (optional)">
        <textarea className="cc-input min-h-[80px]" maxLength={4000} value={operatorNotes} onChange={(e) => setOperatorNotes(e.target.value)} />
      </Field>

      <div className="space-y-2 text-sm">
        <label className="flex items-start gap-3">
          <input type="checkbox" checked={attest} onChange={(e) => setAttest(e.target.checked)} className="mt-1" required />
          <span className="text-stone-300">
            I attest I am the asset owner or otherwise authorized to describe this asset. <span className="text-stone-500">(Required.)</span>
          </span>
        </label>
        <label className="flex items-start gap-3">
          <input type="checkbox" checked={consentDemo} onChange={(e) => setConsentDemo(e.target.checked)} className="mt-1" />
          <span className="text-stone-300">
            Optional · allow a public redacted version of this intake to appear as a demo example. <span className="text-stone-500">(No owner identity included.)</span>
          </span>
        </label>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-500/40 bg-rose-500/[0.05] px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="inline-flex items-center gap-2 px-5 py-3 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] font-semibold tracking-tight disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {submitting ? "Submitting…" : "Submit ComputeClaw intake →"}
      </button>

      <p className="text-xs text-stone-500 leading-relaxed">
        Submitting writes an immutable owner-attested intake record + SHA-256 receipt to the Defendable bakery vault. No final value opinion is issued. No deed is issued. Active eBay listings are observed asking-price evidence only.
      </p>

      <style jsx>{`
        :global(.cc-input),
        :global(.cc-select) {
          width: 100%;
          background: rgb(12 10 9 / 0.6);
          border: 1px solid rgb(41 37 36);
          color: rgb(231 229 228);
          border-radius: 6px;
          padding: 8px 12px;
          font-size: 14px;
        }
        :global(.cc-input:focus),
        :global(.cc-select:focus) {
          outline: none;
          border-color: rgb(246 198 75 / 0.5);
        }
      `}</style>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <div className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold mb-1.5">{label}</div>
      {children}
    </label>
  );
}

function Check({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center gap-2">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="text-stone-300">{label}</span>
    </label>
  );
}
