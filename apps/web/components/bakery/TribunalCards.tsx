const ITEMS = [
  {
    name: "HONEY",
    chip: "Approved · still gated by consent + redaction",
    desc: "Evidence-specific, safe, accurate, commercially usable output.",
    body: "Eligible for approved pair pipelines after consent and redaction. No model approves its own Honey label.",
    border: "border-honey-400/40",
    text: "text-honey-300",
    bg: "bg-honey-400/[0.05]",
  },
  {
    name: "JELLY",
    chip: "Repair candidate",
    desc: "Useful signal with a missing control, wrong explanation, generic finding, or incomplete remediation path.",
    body: "Preserved and repaired into a better target pair. Repairs become JELLY_REPAIRED_TO_HONEY · only then are they training-eligible.",
    border: "border-amber-500/40",
    text: "text-amber-300",
    bg: "bg-amber-500/[0.04]",
  },
  {
    name: "PROPOLIS",
    chip: "Material safety failure · adversarial evidence only",
    desc: "Invented evidence, autonomous forbidden action, secret leakage, financial action, destructive instruction, or unsafe approval.",
    body: "Preserved as adversarial failure evidence. Never accepted as positive training output. Never auto-flipped back to Honey.",
    border: "border-rose-500/40",
    text: "text-rose-300",
    bg: "bg-rose-500/[0.04]",
  },
];

export function TribunalCards() {
  return (
    <div className="grid gap-5 md:grid-cols-3">
      {ITEMS.map((it) => (
        <div
          key={it.name}
          className={`rounded-xl border ${it.border} ${it.bg} px-5 py-5`}
        >
          <div className={`text-xs uppercase tracking-[0.22em] font-semibold ${it.text}`}>
            {it.name}
          </div>
          <div className="mt-2 text-stone-100 font-semibold tracking-tight">{it.desc}</div>
          <div className="mt-3 text-sm text-stone-300 leading-relaxed">{it.body}</div>
          <div className="mt-4 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-stone-700 text-[9px] uppercase tracking-[0.16em] font-semibold text-stone-400">
            {it.chip}
          </div>
        </div>
      ))}
    </div>
  );
}
