/**
 * Truthful Kimi swarm role-status table.
 *
 * Per the Finality Lock doctrine: we do not let public/admin UI imply
 * "all 6 Kimi agents are live." Reality: 1 of 6 (Intake) is wired to
 * Kimi K2.6. The other 5 are scaffolded roles that the platform's
 * deterministic Tribunal/Validator code currently fills.
 */
const ROLES = [
  {
    name: "Intake",
    kimi: "LIVE (Kimi K2.6)",
    determ: "—",
    note: "Conversational ClawCheck front door · 5-dimension capture",
  },
  {
    name: "Inspector",
    kimi: "Scaffolded",
    determ: "—",
    note: "Future: routes captured asset to defendable-compute inspect",
  },
  {
    name: "Benchmarker",
    kimi: "Scaffolded",
    determ: "Operational via defendable-agentgrade CLI",
    note: "Pack execution + receipt assembly works · LLM judge optional",
  },
  {
    name: "Tribunal",
    kimi: "Scaffolded as Kimi role",
    determ: "Operational (deterministic rule layer)",
    note: "Honey/Jelly/Propolis state machine + 12-check Validator chain",
  },
  {
    name: "Validator",
    kimi: "Scaffolded as Kimi role",
    determ: "Operational (12-check pure-code doctrine)",
    note: "Pair candidates advance/quarantine via /admin/validator-review",
  },
  {
    name: "Deedmaker",
    kimi: "Scaffolded",
    determ: "—",
    note: "Future: bundle assembly + SHA-256 manifest + ENS draft",
  },
];

export function RoleStatusTable() {
  return (
    <div className="rounded-xl border border-stone-800 bg-stone-900/60 px-5 py-5">
      <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">
        Kimi swarm · honest role status
      </div>
      <div className="mt-2 text-stone-100 font-semibold tracking-tight">
        ClawCheck intake and the receipt-backed evaluation workflow are operational.
      </div>
      <p className="mt-2 text-xs text-stone-400 leading-relaxed">
        Of the 6 Kimi swarm roles · only Intake currently calls a live Kimi model.
        The other 5 are scaffolded roles · several are operationally covered by
        the platform's deterministic Tribunal + Validator code (not by an LLM).
      </p>

      <div className="mt-5 overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">
              <th className="text-left py-2 pr-3 font-semibold">Role</th>
              <th className="text-left py-2 pr-3 font-semibold">Kimi agent</th>
              <th className="text-left py-2 pr-3 font-semibold">Deterministic platform code</th>
              <th className="text-left py-2 font-semibold">Note</th>
            </tr>
          </thead>
          <tbody className="text-stone-300">
            {ROLES.map((r) => (
              <tr key={r.name} className="border-t border-stone-800/60">
                <td className="py-2 pr-3 font-mono">{r.name}</td>
                <td className="py-2 pr-3">
                  {r.kimi.startsWith("LIVE") ? (
                    <span className="text-honey-300 font-semibold">{r.kimi}</span>
                  ) : (
                    <span className="text-stone-500">{r.kimi}</span>
                  )}
                </td>
                <td className="py-2 pr-3">
                  {r.determ.startsWith("Operational") ? (
                    <span className="text-emerald-300">{r.determ}</span>
                  ) : (
                    <span className="text-stone-500">{r.determ}</span>
                  )}
                </td>
                <td className="py-2 text-stone-400">{r.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
