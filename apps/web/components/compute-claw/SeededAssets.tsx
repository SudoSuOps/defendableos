const ASSETS = [
  {
    name: "NVIDIA RTX 3090 24GB",
    category: "workhorse_gpu",
    market: "DEMO_READY",
    bench: "NOT_YET_ATTACHED",
    utility: "OPTIONAL",
    aiov: "INTAKE_ONLY",
  },
  {
    name: "NVIDIA RTX 5090 32GB",
    category: "premium_agent_gpu",
    market: "DEMO_READY",
    bench: "NOT_YET_ATTACHED",
    utility: "OPTIONAL",
    aiov: "INTAKE_ONLY",
  },
  {
    name: "NVIDIA RTX PRO 6000 Blackwell 96GB",
    category: "premium_agent_gpu",
    market: "DEMO_READY",
    bench: "REQUIRED_FOR_CONDITION_CLAIM",
    utility: "OPTIONAL",
    aiov: "INTAKE_ONLY",
  },
];

export function SeededAssets() {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {ASSETS.map((a) => (
        <div key={a.name} className="rounded-xl border border-stone-800 bg-stone-900/60 px-5 py-5 flex flex-col">
          <div className="flex items-center justify-between gap-3">
            <div className="text-stone-100 font-semibold tracking-tight">{a.name}</div>
            <span className="inline-flex items-center px-2.5 py-1 rounded-full border border-honey-400/40 text-honey-300 bg-honey-400/[0.05] text-[9px] uppercase tracking-[0.16em] font-semibold">
              Demo
            </span>
          </div>
          <div className="mt-1 text-xs text-stone-500 font-mono">{a.category}</div>

          <div className="mt-4 grid grid-cols-2 gap-2 text-[10px] uppercase tracking-[0.14em]">
            <div className="rounded border border-stone-800 bg-stone-950/50 px-2 py-2">
              <div className="text-stone-500 font-semibold">Market Evidence</div>
              <div className="text-stone-200 mt-0.5 normal-case tracking-normal text-xs">{a.market.replace(/_/g, " ")}</div>
            </div>
            <div className="rounded border border-stone-800 bg-stone-950/50 px-2 py-2">
              <div className="text-stone-500 font-semibold">Benchmark</div>
              <div className="text-stone-200 mt-0.5 normal-case tracking-normal text-xs">{a.bench.replace(/_/g, " ")}</div>
            </div>
            <div className="rounded border border-stone-800 bg-stone-950/50 px-2 py-2">
              <div className="text-stone-500 font-semibold">Utility</div>
              <div className="text-stone-200 mt-0.5 normal-case tracking-normal text-xs">{a.utility}</div>
            </div>
            <div className="rounded border border-stone-800 bg-stone-950/50 px-2 py-2">
              <div className="text-stone-500 font-semibold">AIOV</div>
              <div className="text-stone-200 mt-0.5 normal-case tracking-normal text-xs">{a.aiov.replace(/_/g, " ")}</div>
            </div>
          </div>
          <div className="mt-3 text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">
            Controlled Demonstration · Not Customer Production Evidence
          </div>
        </div>
      ))}
    </div>
  );
}
