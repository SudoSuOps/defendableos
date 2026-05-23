const STAGES = [
  { name: "Asset Intake", desc: "Owner-attested asset facts captured immutably." },
  { name: "Observed eBay Market Evidence", desc: "Active-listing asking prices · NOT sold comps." },
  { name: "Noise Exclusion", desc: "Box-only · for-parts · broken · accessories filtered with reason codes." },
  { name: "Benchmark Receipt", desc: "Defendable Box machine-tested condition + performance evidence." },
  { name: "Utility Signal", desc: "Verified rental/income receipts from Vast.ai or Defendable Fleet." },
  { name: "AIOV Draft", desc: "Evidence summary · NEVER a final value opinion." },
  { name: "Validator Review", desc: "Out-of-band human review · 12-check doctrine." },
  { name: "Defendable Compute Deed", desc: "Eligibility review only · NEVER auto-issued." },
];

export function EvidenceStack() {
  return (
    <ol className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {STAGES.map((s, i) => (
        <li key={s.name} className="rounded-xl border border-stone-800 bg-stone-900/60 px-4 py-4">
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-honey-400 font-semibold">
            <span className="inline-flex w-5 h-5 items-center justify-center rounded-full border border-honey-400/40 text-honey-300 text-[10px]">
              {String(i + 1).padStart(2, "0")}
            </span>
            Stage
          </div>
          <div className="mt-2 text-stone-100 font-semibold tracking-tight">{s.name}</div>
          <div className="mt-1.5 text-xs text-stone-400 leading-relaxed">{s.desc}</div>
        </li>
      ))}
    </ol>
  );
}
