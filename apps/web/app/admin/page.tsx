"use client";

import Link from "next/link";

import { Card } from "@/components/ui/Card";

export default function AdminHome() {
  return (
    <div className="max-w-6xl mx-auto w-full px-6 py-10">
      <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">Admin</div>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-100">Review console</h1>
      <p className="text-sm text-stone-400 mt-1.5">
        Platform-admin actions. Every approval, publication, and ENS reservation
        writes an audit event.
      </p>

      <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <AdminLink href="/portal/assets" title="Asset review queue" subtitle="Assets awaiting validator + packaging." />
        <AdminLink href="/portal/edge" title="Edge devices" subtitle="Enrollment, heartbeat, revocation." />
        <AdminLink href="#" title="ENS reservations" subtitle="Mock-mode by default · onchain gated." />
      </div>

      <div className="mt-10">
        <Card title="ENS live-write safety">
          <p className="text-sm text-stone-300 leading-relaxed">
            The mock ENS adapter does <span className="font-semibold">not</span> touch a chain. Issuance requires
            <span className="font-mono"> ENS_LIVE_WRITES_ENABLED=true</span> + a signer key on the server. The
            UI does not surface a signer key field anywhere.
          </p>
        </Card>
      </div>
    </div>
  );
}

function AdminLink({ href, title, subtitle }: { href: string; title: string; subtitle: string }) {
  return (
    <Link
      href={href}
      className="block rounded-xl border border-stone-800 bg-stone-900/60 px-5 py-4 hover:border-honey-400/40"
    >
      <div className="text-stone-100 font-semibold tracking-tight">{title}</div>
      <div className="text-xs text-stone-500 mt-1">{subtitle}</div>
    </Link>
  );
}
