const ITEMS = [
  { name: "Claw Exposure Snapshot", what: "Preliminary intake and risk tier." },
  { name: "ClawCheck Pro", what: "Permission review, control map and remediation findings." },
  { name: "AgentGrade Benchmark", what: "Real-work and adversarial performance testing." },
  { name: "Defendable Agent Deed", what: "Defined-lane verified agent performance record." },
  { name: "AI Work Unit Deed", what: "Agent + deployed compute + controls + economics + recovery package." },
  { name: "AIOV Agent Opinion", what: "Value-supporting analysis for a verified AI operating asset." },
];

export function ProductLadder() {
  return (
    <ol className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
      {ITEMS.map((it, i) => (
        <li
          key={it.name}
          className="rounded-xl border border-stone-800 bg-stone-900/60 px-4 py-4"
        >
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-honey-400 font-semibold">
            <span className="inline-flex w-5 h-5 items-center justify-center rounded-full border border-honey-400/40 text-honey-300 text-[10px]">
              {String(i + 1).padStart(2, "0")}
            </span>
            Tier
          </div>
          <div className="mt-2 text-stone-100 font-semibold tracking-tight">{it.name}</div>
          <div className="mt-1.5 text-xs text-stone-400 leading-relaxed">{it.what}</div>
        </li>
      ))}
    </ol>
  );
}
