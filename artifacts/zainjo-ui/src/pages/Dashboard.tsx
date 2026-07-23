import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";
import api from "../api/client";
import type { DashboardStats } from "../api/types";
import { fmtDate, fmtNumber, severityClass } from "../utils/format";
import {
  Inbox, CheckCircle, XCircle, Send, Server, Filter, RefreshCw,
} from "lucide-react";

const VENDOR_COLORS: Record<string, string> = {
  huawei: "#ef4444",
  nokia: "#3b82f6",
  ericsson: "#a855f7",
  unknown: "#64748b",
};

function StatCard({ icon: Icon, label, value, sub, color }: {
  icon: React.ElementType; label: string; value: string | number; sub?: string; color: string;
}) {
  return (
    <div className="card flex items-start gap-4">
      <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="text-xs text-slate-500 font-medium">{label}</p>
        <p className="text-2xl font-bold text-white mt-0.5">{fmtNumber(Number(value))}</p>
        {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data, isLoading, refetch, isFetching } = useQuery<DashboardStats>({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardStats>("/dashboard/stats").then(r => r.data),
    refetchInterval: 30_000,
  });

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

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Overview</h1>
          <p className="text-sm text-slate-500 mt-0.5">Real-time syslog ingestion statistics</p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="btn-secondary flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${isFetching ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Inbox}       label="Total Received"    value={s.total_received}  color="bg-slate-700" />
        <StatCard icon={CheckCircle} label="Accepted"          value={s.total_accepted}  color="bg-emerald-700" />
        <StatCard icon={XCircle}     label="Dropped"           value={s.total_dropped}   color="bg-red-700" />
        <StatCard icon={Send}        label="Forwarded to SIEM" value={s.total_forwarded} color="bg-brand-700" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard icon={Server} label="Active Sources" value={`${s.active_sources} / ${s.total_sources}`} color="bg-blue-700" />
        <StatCard icon={Filter} label="Active Filter Rules" value={s.active_filter_rules} color="bg-amber-700" />
        <StatCard
          icon={XCircle}
          label="Drop Rate"
          value={s.total_received > 0 ? `${((s.total_dropped / s.total_received) * 100).toFixed(1)}%` : "0%"}
          color="bg-rose-800"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bar: logs by source */}
        <div className="lg:col-span-2 card">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">Logs by Source</h2>
          {s.logs_by_source.length === 0 ? (
            <p className="text-slate-600 text-sm py-8 text-center">No data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={s.logs_by_source} layout="vertical" margin={{ left: 80 }}>
                <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 11 }} tickLine={false} />
                <YAxis type="category" dataKey="source_name" tick={{ fill: "#94a3b8", fontSize: 11 }} width={80} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: "#e2e8f0" }}
                />
                <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Pie: logs by vendor */}
        <div className="card">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">Logs by Vendor</h2>
          {pieData.length === 0 ? (
            <p className="text-slate-600 text-sm py-8 text-center">No data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={false}>
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }}
                />
                <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top users */}
        <div className="card">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">Top Users (Accepted Logs)</h2>
          {s.top_users.length === 0 ? (
            <p className="text-slate-600 text-sm py-4 text-center">No data yet</p>
          ) : (
            <div className="space-y-2">
              {s.top_users.slice(0, 8).map((u) => (
                <div key={u.username} className="flex items-center gap-3">
                  <span className="text-sm text-slate-300 font-mono flex-1 truncate">{u.username}</span>
                  <div className="flex-1 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-brand-500 h-full rounded-full"
                      style={{ width: `${(u.count / s.top_users[0].count) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-400 w-12 text-right">{fmtNumber(u.count)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent events */}
        <div className="card">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">Recent Events</h2>
          <div className="overflow-auto max-h-64">
            <table className="w-full text-xs">
              <thead>
                <tr>
                  <th className="text-left text-slate-500 pb-2 pr-3 font-medium">Time</th>
                  <th className="text-left text-slate-500 pb-2 pr-3 font-medium">Source</th>
                  <th className="text-left text-slate-500 pb-2 pr-3 font-medium">Severity</th>
                  <th className="text-left text-slate-500 pb-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {s.recent_events.map((e) => (
                  <tr key={e.id} className="border-t border-slate-800">
                    <td className="py-1.5 pr-3 text-slate-400 whitespace-nowrap font-mono">{fmtDate(e.received_at).slice(11)}</td>
                    <td className="py-1.5 pr-3 text-slate-300 truncate max-w-[100px]">{e.source_name || e.received_at}</td>
                    <td className="py-1.5 pr-3">
                      <span className={severityClass(e.severity_name)}>{e.severity_name || "—"}</span>
                    </td>
                    <td className="py-1.5">
                      {e.is_dropped
                        ? <span className="badge-red">Dropped</span>
                        : <span className="badge-green">OK</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
