"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Wordmark } from "@/components/brand/Wordmark";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@swarmandbee.ai");
  const [password, setPassword] = useState("defendable-demo");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const out = await api<{ access_token: string }>("/api/v1/auth/login", {
        method: "POST",
        json: { email, password },
        skipAuth: true,
      });
      setToken(out.access_token);
      router.push("/portal");
    } catch (err: any) {
      setError(err?.message ?? "sign-in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-md">
        <div className="mb-10 flex justify-center"><Wordmark /></div>
        <div className="deed-card rounded-xl p-8">
          <h1 className="text-2xl font-semibold tracking-tight text-stone-100">Sign in</h1>
          <p className="text-sm text-stone-400 mt-1.5">Portal access for verified operators.</p>

          <form className="mt-7 space-y-4" onSubmit={onSubmit}>
            <label className="block text-sm">
              <span className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">Email</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full px-4 py-3 rounded bg-stone-950 border border-stone-800 text-stone-100 outline-none focus:border-honey-400 focus:ring-1 focus:ring-honey-400/30"
                required
                autoComplete="email"
              />
            </label>
            <label className="block text-sm">
              <span className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-semibold">Password</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full px-4 py-3 rounded bg-stone-950 border border-stone-800 text-stone-100 outline-none focus:border-honey-400 focus:ring-1 focus:ring-honey-400/30"
                required
                autoComplete="current-password"
              />
            </label>
            {error && <div className="text-xs text-rose-400">{error}</div>}
            <button
              type="submit"
              disabled={busy}
              className="w-full px-5 py-3 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] font-semibold tracking-tight disabled:opacity-50"
            >
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div className="mt-6 text-xs text-stone-500 text-center">
            Local dev seed: <span className="font-mono">demo@swarmandbee.ai</span> · <span className="font-mono">defendable-demo</span>
          </div>
        </div>
      </div>
    </main>
  );
}
