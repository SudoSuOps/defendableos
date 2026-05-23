const CATEGORIES = [
  {
    title: "GPU Cards",
    skus: "RTX 3090 · RTX 5090 · RTX PRO 6000 · A6000 · V100 · A100",
  },
  {
    title: "AI Workstations",
    skus: "Single or multi-GPU machines built for inference, training or rental.",
  },
  {
    title: "Edge Devices",
    skus: "Jetson · ZimaBoard · compact local AI endpoints.",
  },
  {
    title: "Infrastructure",
    skus: "Storage · networking · chassis · server-grade components.",
  },
];

export function CategoryCards() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {CATEGORIES.map((c) => (
        <div key={c.title} className="rounded-xl border border-stone-800 bg-stone-900/60 px-4 py-4">
          <div className="text-stone-100 font-semibold tracking-tight">{c.title}</div>
          <div className="mt-2 text-sm text-stone-400 leading-relaxed">{c.skus}</div>
        </div>
      ))}
    </div>
  );
}
