const STAGES = [
  {
    name: "Intake",
    label: "The agent collects facts. It does not certify itself.",
  },
  {
    name: "Risk Snapshot",
    label: "Platform rules assign a preliminary exposure tier.",
  },
  {
    name: "Validator",
    label: "A separate review layer checks whether every finding matches the evidence.",
  },
  {
    name: "Tribunal",
    label: "Honey, Jelly, or Propolis labels determine how the record is handled.",
  },
  {
    name: "Pair Factory",
    label: "Approved or repaired records become structured training/evaluation candidates.",
  },
  {
    name: "Object Vault",
    label: "Raw evidence, receipts, manifests, and approved corpora are stored separately.",
  },
  {
    name: "Dataset Release",
    label: "Only redacted, consented, Tribunal-approved records enter versioned releases.",
  },
  {
    name: "Specialist Agent",
    label: "Future agents train only from approved datasets and must beat sealed holdouts.",
  },
];

export function PipelineRail() {
  return (
    <div className="relative">
      <ol className="grid gap-4 lg:gap-5 md:grid-cols-2 lg:grid-cols-4">
        {STAGES.map((s, i) => (
          <li
            key={s.name}
            className="relative rounded-xl border border-stone-800 bg-stone-900/60 px-4 py-4"
          >
            <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-honey-400 font-semibold">
              <span className="inline-flex w-5 h-5 items-center justify-center rounded-full border border-honey-400/40 text-honey-300 text-[10px]">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span>Stage</span>
            </div>
            <div className="mt-2 text-stone-100 font-semibold tracking-tight">{s.name}</div>
            <div className="mt-1.5 text-xs text-stone-400 leading-relaxed">{s.label}</div>
          </li>
        ))}
      </ol>
      <div className="mt-6 text-[10px] uppercase tracking-[0.22em] text-stone-500 font-semibold">
        Intake → Risk Snapshot → Validator → Tribunal → Pair Factory → Object Vault → Dataset Release → Specialist Agent
      </div>
    </div>
  );
}
