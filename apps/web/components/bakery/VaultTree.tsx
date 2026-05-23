const TREE = `defendable-claw-bakery/
├── raw-evidence/
│   ├── intakes/
│   ├── snapshots/
│   └── validator-reviews/
├── redacted/
│   ├── approved-for-evaluation/
│   └── approved-for-training/
├── pair-candidates/
│   ├── pending/
│   ├── honey/
│   ├── jelly/
│   ├── jelly-repaired/
│   ├── propolis-failures/
│   └── quarantined/
├── benchmark-packs/
│   ├── business_agent_v1/
│   ├── refund_agent_v1/
│   └── coding_ops_agent_v1/
├── holdouts/
│   ├── sealed/
│   └── manifests/
├── dataset-releases/
├── receipts/
│   ├── sha256/
│   ├── manifests/
│   └── merkle-ready/
└── deeds/
    ├── draft/
    ├── eligible/
    ├── issued/
    └── denied/`;

export function VaultTree() {
  return (
    <div className="rounded-xl border border-stone-800 bg-stone-950/80 px-5 py-5 overflow-x-auto">
      <pre className="text-xs md:text-sm text-stone-300 font-mono leading-relaxed whitespace-pre">
        {TREE}
      </pre>
    </div>
  );
}
