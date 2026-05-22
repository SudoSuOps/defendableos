"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Wordmark } from "@/components/brand/Wordmark";
import { api, getToken, setToken } from "@/lib/api";

interface MeOut {
  user: { id: string; email: string; name: string | null; is_platform_admin: boolean };
  memberships: { organization_id: string; role: string }[];
}

interface OrgOut {
  id: string;
  name: string;
  slug: string;
  ens_label: string | null;
  ens_name: string | null;
  ens_status: string;
}

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [me, setMe] = useState<MeOut | null>(null);
  const [org, setOrg] = useState<OrgOut | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    (async () => {
      try {
        const [meOut, orgOut] = await Promise.all([
          api<MeOut>("/api/v1/me"),
          api<OrgOut>("/api/v1/organizations/current"),
        ]);
        setMe(meOut);
        setOrg(orgOut);
      } catch {
        setToken(null);
        router.replace("/login");
        return;
      }
      setReady(true);
    })();
  }, [router]);

  if (!ready) {
    return (
      <main className="min-h-screen flex items-center justify-center text-stone-500 text-sm">
        Loading portal…
      </main>
    );
  }

  const nav = [
    { href: "/portal", label: "Dashboard" },
    { href: "/portal/assets", label: "Assets" },
    { href: "/portal/edge", label: "Edge Devices" },
    ...(me?.user.is_platform_admin ? [{ href: "/admin", label: "Admin" }] : []),
  ];

  return (
    <main className="min-h-screen flex flex-col">
      <header className="px-6 py-4 border-b border-stone-900/80 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/portal"><Wordmark /></Link>
          <nav className="flex items-center gap-1 text-sm">
            {nav.map((n) => {
              const active = pathname === n.href || pathname.startsWith(n.href + "/");
              return (
                <Link
                  key={n.href}
                  href={n.href}
                  className={`px-3 py-1.5 rounded ${
                    active ? "bg-stone-900 text-stone-100" : "text-stone-400 hover:text-stone-200"
                  }`}
                >
                  {n.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-4 text-xs text-stone-500">
          {org && (
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded-full border border-stone-700 text-stone-300 font-mono text-[11px]">
                {org.ens_name ?? org.slug}
              </span>
              <span className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">
                {org.ens_status}
              </span>
            </div>
          )}
          <button
            onClick={() => {
              setToken(null);
              router.push("/login");
            }}
            className="text-stone-400 hover:text-stone-200"
          >
            Sign out
          </button>
        </div>
      </header>
      {children}
    </main>
  );
}
