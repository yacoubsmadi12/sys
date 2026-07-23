import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../api/client";
import {
  Settings2, Save, RefreshCw, HardDrive, Clock, Cpu, Database,
  Radio, RotateCcw, CheckCircle, AlertTriangle, Info,
} from "lucide-react";

interface Policy {
  retention_days: number;
  compress_after_days: number;
  syslog_workers: number;
  syslog_queue_size: number;
  siem_enabled: boolean;
  siem_batch_size: number;
  siem_url: string;
  storage_path: string;
}

function Field({
  label, hint, icon: Icon, children,
}: {
  label: string; hint?: string; icon: React.ElementType; children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-4 py-5 border-b border-slate-800 last:border-0">
      <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Icon className="w-4 h-4 text-slate-400" />
      </div>
      <div className="flex-1 min-w-0">
        <label className="block text-sm font-medium text-slate-200 mb-1">{label}</label>
        {hint && <p className="text-xs text-slate-500 mb-2">{hint}</p>}
        {children}
      </div>
    </div>
  );
}

function NumInput({
  value, onChange, min, max, unit,
}: {
  value: number; onChange: (v: number) => void; min?: number; max?: number; unit?: string;
}) {
  return (
    <div className="flex items-center gap-2 w-full max-w-xs">
      <input
        type="number"
        className="input"
        value={value}
        min={min}
        max={max}
        onChange={(e) => onChange(Number(e.target.value))}
      />
      {unit && <span className="text-xs text-slate-500 flex-shrink-0">{unit}</span>}
    </div>
  );
}

export default function Settings() {
  const qc = useQueryClient();

  const { data, isLoading, refetch } = useQuery<Policy>({
    queryKey: ["settings"],
    queryFn: () => api.get<Policy>("/settings").then((r) => r.data),
  });

  const [form, setForm] = useState<Partial<Policy>>({});
  const [saved, setSaved] = useState(false);

  // Merge server data with local edits
  const merged: Policy | null = data ? { ...data, ...form } : null;

  function set<K extends keyof Policy>(k: K, v: Policy[K]) {
    setForm((f) => ({ ...f, [k]: v }));
    setSaved(false);
  }

  const mutation = useMutation({
    mutationFn: (body: Partial<Policy>) =>
      api.patch<Policy>("/settings", body).then((r) => r.data),
    onSuccess: (updated) => {
      qc.setQueryData(["settings"], updated);
      setForm({});
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  function handleSave() {
    if (!form || Object.keys(form).length === 0) return;
    mutation.mutate(form);
  }

  function handleReset() {
    setForm({});
    setSaved(false);
  }

  const isDirty = Object.keys(form).length > 0;

  if (isLoading || !merged) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Settings2 className="w-5 h-5 text-brand-400" />
            System Settings
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Log retention policy &amp; runtime configuration
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          {isDirty && (
            <button onClick={handleReset} className="btn-secondary flex items-center gap-2">
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={!isDirty || mutation.isPending}
            className="btn-primary flex items-center gap-2"
          >
            {mutation.isPending ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Save Changes
          </button>
        </div>
      </div>

      {/* Success banner */}
      {saved && (
        <div className="flex items-center gap-2 bg-emerald-900/30 border border-emerald-800 rounded-lg px-4 py-3 text-emerald-300 text-sm">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          Settings saved to config.yaml — restart the service to apply runtime changes.
        </div>
      )}

      {/* Error banner */}
      {mutation.isError && (
        <div className="flex items-center gap-2 bg-red-900/30 border border-red-800 rounded-lg px-4 py-3 text-red-300 text-sm">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          Failed to save settings. Check your permissions.
        </div>
      )}

      {/* ── Log Retention ── */}
      <div className="card">
        <h2 className="text-sm font-semibold text-slate-300 mb-1 flex items-center gap-2">
          <Clock className="w-4 h-4 text-amber-400" />
          Log Retention Policy
        </h2>
        <p className="text-xs text-slate-500 mb-4">
          Controls how long raw syslog files are kept on disk before deletion or compression.
        </p>

        <Field
          label="Retention Period"
          hint="Raw log files older than this will be permanently deleted by the nightly cleanup job."
          icon={Clock}
        >
          <NumInput
            value={merged.retention_days}
            onChange={(v) => set("retention_days", v)}
            min={1} max={3650} unit="days"
          />
          <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-500">
            <Info className="w-3 h-3" />
            Currently keeping logs for&nbsp;
            <span className="text-slate-300 font-medium">{merged.retention_days} days</span>
            &nbsp;(≈ {(merged.retention_days / 30).toFixed(1)} months)
          </div>
        </Field>

        <Field
          label="Compression Threshold"
          hint="Log files older than this number of days will be gzip-compressed to save disk space."
          icon={HardDrive}
        >
          <NumInput
            value={merged.compress_after_days}
            onChange={(v) => set("compress_after_days", v)}
            min={1} max={365} unit="days"
          />
        </Field>

        <Field
          label="Storage Path"
          hint="Root directory where daily syslog flat-files are written."
          icon={HardDrive}
        >
          <input
            type="text"
            className="input max-w-sm font-mono text-xs"
            value={merged.storage_path}
            onChange={(e) => set("storage_path", e.target.value)}
          />
        </Field>
      </div>

      {/* ── Processing ── */}
      <div className="card">
        <h2 className="text-sm font-semibold text-slate-300 mb-1 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-blue-400" />
          Processing
        </h2>
        <p className="text-xs text-slate-500 mb-4">
          Tune the number of async workers and the in-memory ingestion queue.
        </p>

        <Field
          label="Processor Workers"
          hint="Number of parallel async workers that parse, filter, and store incoming syslog messages. Requires restart."
          icon={Cpu}
        >
          <NumInput
            value={merged.syslog_workers}
            onChange={(v) => set("syslog_workers", v)}
            min={1} max={64} unit="workers"
          />
        </Field>

        <Field
          label="Queue Size"
          hint="Maximum number of syslog messages held in the in-memory queue before back-pressure kicks in."
          icon={Database}
        >
          <NumInput
            value={merged.syslog_queue_size}
            onChange={(v) => set("syslog_queue_size", v)}
            min={1000} max={1000000} unit="messages"
          />
        </Field>
      </div>

      {/* ── SIEM ── */}
      <div className="card">
        <h2 className="text-sm font-semibold text-slate-300 mb-1 flex items-center gap-2">
          <Radio className="w-4 h-4 text-purple-400" />
          SIEM Forwarding
        </h2>
        <p className="text-xs text-slate-500 mb-4">
          Controls whether accepted logs are forwarded to the SIEM system.
        </p>

        <Field
          label="Enable SIEM Forwarding"
          hint="When disabled, logs are still stored locally but not sent to the SIEM endpoint."
          icon={Radio}
        >
          <button
            onClick={() => set("siem_enabled", !merged.siem_enabled)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              merged.siem_enabled ? "bg-brand-600" : "bg-slate-700"
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                merged.siem_enabled ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
          <span className="ml-3 text-xs text-slate-400">
            {merged.siem_enabled ? "Enabled" : "Disabled"}
          </span>
        </Field>

        <Field
          label="SIEM Endpoint URL"
          hint="HTTP endpoint that receives batched log payloads via POST."
          icon={Radio}
        >
          <input
            type="text"
            className="input max-w-sm font-mono text-xs"
            value={merged.siem_url}
            onChange={(e) => set("siem_url", e.target.value)}
            disabled={!merged.siem_enabled}
          />
        </Field>

        <Field
          label="Batch Size"
          hint="Number of log entries per HTTP POST to the SIEM. Larger batches = fewer requests."
          icon={Database}
        >
          <NumInput
            value={merged.siem_batch_size}
            onChange={(v) => set("siem_batch_size", v)}
            min={1} max={5000} unit="logs / batch"
          />
        </Field>
      </div>

      {/* Info note */}
      <div className="flex items-start gap-3 bg-slate-900/60 border border-slate-800 rounded-xl px-4 py-3 text-xs text-slate-500">
        <Info className="w-4 h-4 flex-shrink-0 mt-0.5 text-slate-600" />
        <p>
          Changes are written to <code className="text-slate-400 font-mono">config.yaml</code>.
          Retention &amp; SIEM settings take effect on the next cleanup cycle.
          Worker and queue changes require a service restart.
        </p>
      </div>
    </div>
  );
}
