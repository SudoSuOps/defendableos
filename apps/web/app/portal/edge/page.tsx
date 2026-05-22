"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Card, Chip } from "@/components/ui/Card";
import { api } from "@/lib/api";

interface EdgeNode {
  id: string;
  node_name: string;
  node_slug: string;
  enrollment_status: string;
  last_heartbeat_at: string | null;
  software_version: string | null;
  created_at: string;
}

const STATUS_TONE: Record<string, "ok" | "pending" | "warn" | "neutral"> = {
  ENROLLED: "ok",
  ENROLLED_DEMO: "ok",
  PENDING: "pending",
  STALE: "warn",
  REVOKED: "warn",
};

export default function EdgePage() {
  const [nodes, setNodes] = useState<EdgeNode[]>([]);

  useEffect(() => {
    api<EdgeNode[]>("/api/v1/edge/nodes").then(setNodes).catch(() => setNodes([]));
  }, []);

  return (
    <div className="max-w-7xl mx-auto w-full px-6 py-10">
      <div className="flex items-baseline justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">Edge</div>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-100">Defendable Boxes</h1>
          <p className="text-sm text-stone-400 mt-1.5">
            Local capture · verified receipts · sovereign evidence flow.
          </p>
        </div>
        <Link
          href="/portal/edge/enroll"
          className="px-4 py-2.5 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] text-sm font-semibold"
        >
          + Enroll device
        </Link>
      </div>

      <div className="mt-8">
        <Card>
          {nodes.length === 0 ? (
            <div className="text-sm text-stone-500 py-8 text-center">No edge devices yet.</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">
                <tr>
                  <th className="text-left py-2">Node</th>
                  <th className="text-left py-2">Slug</th>
                  <th className="text-left py-2">Status</th>
                  <th className="text-left py-2">Last heartbeat</th>
                  <th className="text-left py-2">Agent</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-900">
                {nodes.map((n) => (
                  <tr key={n.id}>
                    <td className="py-3 text-stone-100">{n.node_name}</td>
                    <td className="py-3 font-mono text-stone-300">{n.node_slug}</td>
                    <td className="py-3"><Chip tone={STATUS_TONE[n.enrollment_status] ?? "neutral"}>{n.enrollment_status}</Chip></td>
                    <td className="py-3 text-stone-400">
                      {n.last_heartbeat_at ? new Date(n.last_heartbeat_at).toLocaleString() : "—"}
                    </td>
                    <td className="py-3 text-stone-400">{n.software_version ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </div>
  );
}
