const TIERS = [
  { name: "Compute Intake Snapshot", what: "Free preliminary evidence checklist." },
  { name: "Observed Market Evidence Pack", what: "Timestamped, normalized active-listing observations with receipts." },
  { name: "Defendable Benchmark Review", what: "Machine identity and performance evidence." },
  { name: "Compute Proof Pack", what: "Market context + benchmark + utility evidence + AIOV draft." },
  { name: "Defendable Compute Deed", what: "Validator-approved asset record for defined purposes." },
];

export function ComputeClawProductLadder() {
  return (
    <ol className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
      {TIERS.map((t, i) => (
        <li key={t.name} className="rounded-xl border border-stone-800 bg-stone-900/60 px-4 py-4">
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-honey-400 font-semibold">
            <span className="inline-flex w-5 h-5 items-center justify-center rounded-full border border-honey-400/40 text-honey-300 text-[10px]">
              {String(i + 1).padStart(2, "0")}
            </span>
            Tier
          </div>
          <div className="mt-2 text-stone-100 font-semibold tracking-tight">{t.name}</div>
          <div className="mt-1.5 text-xs text-stone-400 leading-relaxed">{t.what}</div>
        </li>
      ))}
    </ol>
  );
}
