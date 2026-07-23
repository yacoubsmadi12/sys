import { useMutation, useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";
import api from "../api/client";
import type { DashboardStats } from "../api/types";
import { fmtDate, fmtNumber, severityClass } from "../utils/format";
import {
  Activity, ArrowDownRight, ArrowUpRight, CheckCircle, CircleGauge,
  Filter, Inbox, RefreshCw, Radio, Send, Server, ShieldAlert, Trash2,
  UserRound, Wifi, XCircle, Zap, AlertTriangle,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";

const VENDOR_COLORS: Record<string, string> = {
  huawei: "#ef4444",
  nokia: "#3b82f6",
  ericsson: "#a855f7",
  unknown: "#64748b",
};

function StatCard({ icon: Icon, label, value, sub, color, tone = "default" }: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sub?: string;
  color: string;
  tone?: "default" | "positive" | "warning" | "danger";
}) {
  const valueColor = {
    default: "text-white",
    positive: "text-emerald-300",
    warning: "text-amber-300",
    danger: "text-rose-300",
  }[tone];

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-slate-800/90 bg-slate-900/80 p-5 shadow-[0_14px_40px_rgba(2,6,23,0.2)] transition-all hover:-translate-y-0.5 hover:border-slate-700">
      <div className={`absolute -right-8 -top-8 h-28 w-28 rounded-full blur-3xl opacity-20 ${color}`} />
      <div className="relative flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</p>
          <p className={`mt-3 text-3xl font-bold tracking-tight ${valueColor}`}>{typeof value === "number" ? fmtNumber(value) : value}</p>
          {sub && <p className="mt-1.5 text-xs text-slate-500">{sub}</p>}
        </div>
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/10 ${color} shadow-lg`}>
          <Icon className="h-5 w-5 text-white" />
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { isAdmin } = useAuth();
  const { data, isLoading, refetch, isFetching } = useQuery<DashboardStats>({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardStats>("/dashboard/stats").then(r => r.data),
    refetchInterval: 30_000,
  });
  const deleteAllLogs = useMutation({
    mutationFn: () => api.delete("/logs/all"),
    onSuccess: () => refetch(),
  });

  function handleDeleteAllLogs() {
    if (!window.confirm("Delete all logs from the database and configured storage path? This cannot be undone.")) {
      return;
    }
    if (!window.confirm("Confirm permanent deletion of every collected log and audit record.")) {
      return;
    }
    deleteAllLogs.mutate();
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const s = data!;
  const pieData = s.logs_by_vendor.map(v => ({
    name: v.vendor,
    value: v.count,
    fill: VENDOR_COLORS[v.vendor.toLowerCase()] || "#64748b",
  }));
  const dropRate = s.total_received > 0
    ? `${((s.total_dropped / s.total_received) * 100).toFixed(1)}%`
    : "0.0%";
  const acceptedRate = s.total_received > 0
    ? `${((s.total_accepted / s.total_received) * 100).toFixed(1)}% accepted`
    : "Waiting for incoming logs";

  return (
    <div className="min-h-full bg-[radial-gradient(circle_at_85%_0%,rgba(79,70,229,0.12),transparent_28%),radial-gradient(circle_at_15%_20%,rgba(6,182,212,0.06),transparent_24%)] p-4 sm:p-6">
      <div className="mx-auto max-w-[1600px] space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-brand-400">
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400 shadow-[0_0_12px_#34d399]" />
              Operations center
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">LogStream overview</h1>
            <p className="mt-1.5 text-sm text-slate-400">Monitor ingestion, filtering, and SIEM delivery in real time.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2 rounded-lg border border-emerald-900/60 bg-emerald-950/30 px-3 py-2 text-xs text-emerald-300">
              <Wifi className="h-3.5 w-3.5" />
              {isFetching ? "Syncing data" : "Live connection"}
            </div>
            {isAdmin && (
              <button
                onClick={handleDeleteAllLogs}
                disabled={deleteAllLogs.isPending}
                className="btn-secondary flex items-center gap-2 text-red-400 hover:border-red-800 hover:text-red-300"
              >
                <Trash2 className="h-4 w-4" />
                {deleteAllLogs.isPending ? "Deleting…" : "Delete all logs"}
              </button>
            )}
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="btn-primary flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>
        </div>

        {deleteAllLogs.isError && (
          <div className="flex items-center gap-2 rounded-xl border border-red-800 bg-red-900/30 px-4 py-3 text-sm text-red-300">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            Failed to delete logs. Please try again.
          </div>
        )}

        {/* Primary metrics */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard icon={Inbox} label="Total received" value={s.total_received} sub="All messages in the pipeline" color="bg-slate-700" />
          <StatCard icon={CheckCircle} label="Accepted" value={s.total_accepted} sub={acceptedRate} color="bg-emerald-700" tone="positive" />
          <StatCard icon={ShieldAlert} label="Dropped by filters" value={s.total_dropped} sub="Blocked before forwarding" color="bg-rose-700" tone="danger" />
          <StatCard icon={Send} label="Forwarded to SIEM" value={s.total_forwarded} sub="Successfully delivered" color="bg-brand-700" />
        </div>

        {/* Operational health */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <StatCard icon={Server} label="Active sources" value={`${s.active_sources} / ${s.total_sources}`} sub="Enabled source configurations" color="bg-blue-700" />
          <StatCard icon={Filter} label="Active filter rules" value={s.active_filter_rules} sub="Rules currently enforced" color="bg-amber-700" tone="warning" />
          <StatCard icon={CircleGauge} label="Drop rate" value={dropRate} sub="Share of received logs blocked" color="bg-fuchsia-700" tone="warning" />
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          {/* Bar: logs by source */}
          <div className="rounded-2xl border border-slate-800/90 bg-slate-900/80 p-5 shadow-[0_14px_40px_rgba(2,6,23,0.18)] xl:col-span-2">
            <div className="mb-5 flex items-start justify-between">
              <div>
                <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                  <Activity className="h-4 w-4 text-brand-400" />
                  Logs by source
                </h2>
                <p className="mt-1 text-xs text-slate-500">Top sources by received volume</p>
              </div>
              <span className="rounded-md border border-slate-700 bg-slate-800/70 px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-slate-500">Top 10</span>
            </div>
            {s.logs_by_source.length === 0 ? (
              <p className="py-8 text-center text-sm text-slate-600">No source traffic yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={s.logs_by_source} layout="vertical" margin={{ left: 8, right: 12 }}>
                  <XAxis type="number" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} />
                  <YAxis type="category" dataKey="source_name" tick={{ fill: "#94a3b8", fontSize: 11 }} width={118} tickLine={false} axisLine={false} />
                  <Tooltip
                    cursor={{ fill: "rgba(99,102,241,0.08)" }}
                    contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 10, fontSize: 12 }}
                    labelStyle={{ color: "#e2e8f0" }}
                  />
                  <Bar dataKey="count" fill="#6366f1" radius={[0, 6, 6, 0]} barSize={14} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Pie: logs by vendor */}
          <div className="rounded-2xl border border-slate-800/90 bg-slate-900/80 p-5 shadow-[0_14px_40px_rgba(2,6,23,0.18)]">
            <div className="mb-5">
              <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                <Radio className="h-4 w-4 text-cyan-400" />
                Traffic by vendor
              </h2>
              <p className="mt-1 text-xs text-slate-500">Distribution across detected vendors</p>
            </div>
            {pieData.length === 0 ? (
              <p className="py-8 text-center text-sm text-slate-600">No vendor traffic yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="46%" innerRadius={52} outerRadius={82} paddingAngle={3} stroke="none">
                    {pieData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 10, fontSize: 12 }} />
                  <Legend verticalAlign="bottom" height={30} wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Bottom row */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Top users */}
          <div className="rounded-2xl border border-slate-800/90 bg-slate-900/80 p-5 shadow-[0_14px_40px_rgba(2,6,23,0.18)]">
            <div className="mb-5 flex items-start justify-between">
              <div>
                <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                  <UserRound className="h-4 w-4 text-violet-400" />
                  Top users
                </h2>
                <p className="mt-1 text-xs text-slate-500">Accepted activity by username</p>
              </div>
              <ArrowUpRight className="h-4 w-4 text-slate-600" />
            </div>
            {s.top_users.length === 0 ? (
              <p className="py-4 text-center text-sm text-slate-600">No accepted activity yet</p>
            ) : (
              <div className="space-y-3">
                {s.top_users.slice(0, 8).map((u, index) => (
                  <div key={u.username} className="flex items-center gap-3">
                    <span className="w-5 text-xs font-semibold text-slate-600">{String(index + 1).padStart(2, "0")}</span>
                    <span className="w-28 truncate font-mono text-xs text-slate-300">{u.username}</span>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-800">
                      <div className="h-full rounded-full bg-gradient-to-r from-brand-600 to-cyan-400" style={{ width: `${(u.count / s.top_users[0].count) * 100}%` }} />
                    </div>
                    <span className="w-12 text-right text-xs text-slate-400">{fmtNumber(u.count)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent events */}
          <div className="rounded-2xl border border-slate-800/90 bg-slate-900/80 p-5 shadow-[0_14px_40px_rgba(2,6,23,0.18)]">
            <div className="mb-5 flex items-start justify-between">
              <div>
                <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                  <Zap className="h-4 w-4 text-amber-400" />
                  Recent events
                </h2>
                <p className="mt-1 text-xs text-slate-500">Latest messages moving through the pipeline</p>
              </div>
              <ArrowDownRight className="h-4 w-4 text-slate-600" />
            </div>
            <div className="max-h-64 overflow-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr>
                    <th className="pb-2 pr-3 text-left font-medium text-slate-600">Time</th>
                    <th className="pb-2 pr-3 text-left font-medium text-slate-600">Source</th>
                    <th className="pb-2 pr-3 text-left font-medium text-slate-600">Severity</th>
                    <th className="pb-2 text-left font-medium text-slate-600">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {s.recent_events.map((e) => (
                    <tr key={e.id} className="border-t border-slate-800/80">
                      <td className="whitespace-nowrap py-2 pr-3 font-mono text-slate-500">{fmtDate(e.received_at).slice(11)}</td>
                      <td className="max-w-[130px] truncate py-2 pr-3 text-slate-300">{e.source_name || e.received_at}</td>
                      <td className="py-2 pr-3"><span className={severityClass(e.severity_name)}>{e.severity_name || "—"}</span></td>
                      <td className="py-2">{e.is_dropped ? <span className="badge-red">Dropped</span> : <span className="badge-green">Accepted</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
