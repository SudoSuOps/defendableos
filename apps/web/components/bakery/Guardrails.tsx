const ITEMS = [
  "Raw evidence is immutable.",
  "Private data is not training data by default.",
  "Customer records require consent and redaction.",
  "Generated cases are candidates, not truth.",
  "No agent approves its own Honey label.",
  "Sealed holdouts cannot enter training.",
  "No deed issues without Validator review.",
  "No production model continuously fine-tunes itself from live intake.",
];

export function Guardrails() {
  return (
    <ul className="grid gap-3 md:grid-cols-2">
      {ITEMS.map((it) => (
        <li
          key={it}
          className="flex items-start gap-3 rounded-lg border border-stone-800 bg-stone-900/50 px-4 py-3"
        >
          <span className="text-honey-300 text-xs mt-0.5">◆</span>
          <span className="text-stone-200 text-sm leading-relaxed">{it}</span>
        </li>
      ))}
    </ul>
  );
}
