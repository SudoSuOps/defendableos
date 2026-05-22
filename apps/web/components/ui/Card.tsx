import { clsx } from "clsx";

export function Card({
  children,
  className,
  title,
  subtitle,
  actions,
}: {
  children: React.ReactNode;
  className?: string;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
}) {
  return (
    <div className={clsx("rounded-xl border border-stone-800 bg-stone-900/60", className)}>
      {(title || subtitle || actions) && (
        <div className="flex items-start justify-between px-5 py-4 border-b border-stone-800">
          <div>
            {title && <div className="text-stone-100 font-semibold tracking-tight">{title}</div>}
            {subtitle && <div className="text-xs text-stone-500 mt-0.5">{subtitle}</div>}
          </div>
          {actions}
        </div>
      )}
      <div className="px-5 py-4">{children}</div>
    </div>
  );
}

export function Stat({ label, value, hint }: { label: string; value: React.ReactNode; hint?: string }) {
  return (
    <div className="rounded-lg border border-stone-800 bg-stone-900/40 px-4 py-3">
      <div className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">{label}</div>
      <div className="text-stone-100 text-2xl font-semibold tracking-tight mt-1">{value}</div>
      {hint && <div className="text-xs text-stone-500 mt-1">{hint}</div>}
    </div>
  );
}

export function Chip({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: "neutral" | "ok" | "pending" | "warn";
}) {
  const toneClass = {
    neutral: "border-stone-700 text-stone-300 bg-stone-900/50",
    ok: "border-emerald-500/40 text-emerald-300 bg-emerald-500/[0.06]",
    pending: "border-amber-500/40 text-amber-300 bg-amber-500/[0.06]",
    warn: "border-rose-500/40 text-rose-300 bg-rose-500/[0.06]",
  }[tone];
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[9px] uppercase tracking-[0.16em] font-semibold ${toneClass}`}
    >
      {children}
    </span>
  );
}
