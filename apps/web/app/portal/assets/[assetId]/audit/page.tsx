"use client";

import { use, useEffect, useState } from "react";

import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";

interface AuditEvent {
  id: string;
  actor_type: string;
  actor_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  extra_metadata: any;
  created_at: string;
}

export default function AuditPage({ params }: { params: Promise<{ assetId: string }> }) {
  const { assetId } = use(params);
  const [events, setEvents] = useState<AuditEvent[]>([]);

  useEffect(() => {
    api<AuditEvent[]>(`/api/v1/assets/${assetId}/audit`).then(setEvents).catch(() => setEvents([]));
  }, [assetId]);

  return (
    <Card title="Audit trail" subtitle="Every approval, publication, and edge event is recorded.">
      {events.length === 0 ? (
        <div className="text-sm text-stone-500 py-8 text-center">No events yet.</div>
      ) : (
        <ul className="divide-y divide-stone-900 text-sm">
          {events.map((e) => (
            <li key={e.id} className="py-3 flex items-baseline justify-between gap-4">
              <div>
                <div className="font-mono text-stone-300">{e.action}</div>
                <div className="text-xs text-stone-500">
                  by <span className="font-mono">{e.actor_type}</span>
                  {e.actor_id ? ` (${e.actor_id.slice(0, 8)}…)` : ""}
                </div>
              </div>
              <div className="text-xs text-stone-500">{new Date(e.created_at).toLocaleString()}</div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
