export function Wordmark({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <span className="inline-flex w-7 h-7 rounded border border-honey-400/40 items-center justify-center text-honey-300">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.4">
          <path d="M3 2h6l3 3v8H3z" />
          <path d="M5 6h5M5 8h5M5 10h3" strokeWidth="1" opacity="0.7" />
        </svg>
      </span>
      <div className="flex flex-col leading-none">
        <span className="text-stone-100 font-semibold tracking-tight">DefendableOS</span>
        <span className="text-[10px] uppercase tracking-[0.22em] text-stone-500 font-semibold mt-0.5">
          Proof of Value
        </span>
      </div>
    </div>
  );
}
