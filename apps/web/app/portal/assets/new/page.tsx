"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";

const COMPUTE_CATEGORIES = [
  "GPU_ACCELERATOR",
  "AI_WORKSTATION",
  "GPU_SERVER",
  "EDGE_APPLIANCE",
  "COMPUTE_CLUSTER",
  "OTHER",
];

const INTENDED_USE = [
  "INFERENCE",
  "TRAINING",
  "RENDERING",
  "RENTAL_COMPUTE",
  "EDGE_INFERENCE",
  "GENERAL_AI_WORKLOAD",
];

const CONDITION_STATUS = ["NEW", "USED", "REFURBISHED", "UNKNOWN"];

export default function NewAssetPage() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    const f = new FormData(e.currentTarget);
    const body = {
      name: f.get("name"),
      asset_class: "COMPUTE_HARDWARE",
      category: f.get("category") || null,
      description: f.get("description") || null,
      private_serial_number: f.get("private_serial_number") || null,
      client_internal_reference: f.get("client_internal_reference") || null,
      compute_profile: {
        manufacturer: f.get("manufacturer") || null,
        model: f.get("model") || null,
        gpu_count: f.get("gpu_count") ? Number(f.get("gpu_count")) : null,
        vram_per_gpu_gb: f.get("vram_per_gpu_gb") ? Number(f.get("vram_per_gpu_gb")) : null,
        cpu: f.get("cpu") || null,
        ram_gb: f.get("ram_gb") ? Number(f.get("ram_gb")) : null,
        storage_description: f.get("storage_description") || null,
        networking_description: f.get("networking_description") || null,
        operating_system: f.get("operating_system") || null,
        condition_status: f.get("condition_status") || null,
        operational_status: f.get("operational_status") || null,
        intended_use: f.get("intended_use") || null,
      },
    };
    try {
      const out = await api<{ id: string }>("/api/v1/assets", { method: "POST", json: body });
      router.push(`/portal/assets/${out.id}`);
    } catch (e: any) {
      setErr(e?.message ?? "create failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto w-full px-6 py-10">
      <div className="text-[10px] uppercase tracking-[0.22em] text-honey-400/80 font-semibold">Assets · New</div>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-100">
        Create a compute asset
      </h1>
      <p className="text-sm text-stone-400 mt-1.5">
        COMPUTE_HARDWARE is the first complete vertical. Other asset classes will follow.
      </p>

      <form className="mt-8 space-y-6" onSubmit={onSubmit}>
        <Card title="General">
          <div className="grid sm:grid-cols-2 gap-4">
            <Field name="name" label="Asset name" required />
            <Select name="category" label="Category" options={COMPUTE_CATEGORIES} />
            <Field name="description" label="Description" textarea className="sm:col-span-2" />
            <Field name="client_internal_reference" label="Client internal reference" />
            <Field name="private_serial_number" label="Serial number (private)" hint="Stays server-side · never publicly exposed." />
          </div>
        </Card>

        <Card title="Compute identity">
          <div className="grid sm:grid-cols-2 gap-4">
            <Field name="manufacturer" label="Manufacturer" placeholder="NVIDIA" />
            <Field name="model" label="Model" placeholder="RTX PRO 6000 Blackwell" />
            <Field name="gpu_count" label="GPU count" type="number" />
            <Field name="vram_per_gpu_gb" label="VRAM per GPU (GB)" type="number" />
            <Field name="cpu" label="CPU" />
            <Field name="ram_gb" label="RAM (GB)" type="number" />
            <Field name="storage_description" label="Storage" />
            <Field name="networking_description" label="Networking" />
            <Field name="operating_system" label="OS" />
            <Select name="intended_use" label="Intended use" options={INTENDED_USE} />
          </div>
        </Card>

        <Card title="Condition">
          <div className="grid sm:grid-cols-2 gap-4">
            <Select name="condition_status" label="Condition" options={CONDITION_STATUS} />
            <Field name="operational_status" label="Operational status" placeholder="OPERATIONAL" />
          </div>
        </Card>

        {err && <div className="text-sm text-rose-400">{err}</div>}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={busy}
            className="px-5 py-3 rounded border border-honey-400/50 text-honey-200 hover:bg-honey-400/[0.08] font-semibold disabled:opacity-50"
          >
            {busy ? "Creating…" : "Create asset"}
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({
  name, label, hint, required, textarea, type, placeholder, className,
}: {
  name: string; label: string; hint?: string; required?: boolean;
  textarea?: boolean; type?: string; placeholder?: string; className?: string;
}) {
  return (
    <label className={`block text-sm ${className ?? ""}`}>
      <span className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">{label}</span>
      {textarea ? (
        <textarea
          name={name}
          placeholder={placeholder}
          required={required}
          rows={3}
          className="mt-1 w-full px-3 py-2 rounded bg-stone-950 border border-stone-800 text-stone-100 outline-none focus:border-honey-400"
        />
      ) : (
        <input
          name={name}
          type={type ?? "text"}
          placeholder={placeholder}
          required={required}
          className="mt-1 w-full px-3 py-2 rounded bg-stone-950 border border-stone-800 text-stone-100 outline-none focus:border-honey-400"
        />
      )}
      {hint && <span className="text-[11px] text-stone-500 mt-1 block">{hint}</span>}
    </label>
  );
}

function Select({ name, label, options }: { name: string; label: string; options: string[] }) {
  return (
    <label className="block text-sm">
      <span className="text-[10px] uppercase tracking-[0.16em] text-stone-500 font-semibold">{label}</span>
      <select
        name={name}
        defaultValue=""
        className="mt-1 w-full px-3 py-2 rounded bg-stone-950 border border-stone-800 text-stone-100 outline-none focus:border-honey-400"
      >
        <option value="">—</option>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );
}
