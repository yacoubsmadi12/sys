import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import type { AuditLog, PaginatedResponse } from "../api/types";
import { fmtDate, vendorClass } from "../utils/format";
import { FileWarning, Search, X, ChevronLeft, ChevronRight, Eye } from "lucide-react";

interface Filters {
  source_name: string; username: string; vendor: string;
  rule_name: string; from_date: string; to_date: string;
}
const EMPTY: Filters = { source_name: "", username: "", vendor: "", rule_name: "", from_date: "", to_date: "" };

export default function Audit() {
  const [filters, setFilters] = useState<Filters>(EMPTY);
  const [applied, setApplied] = useState<Filters>(EMPTY);
  const [page, setPage]       = useState(1);
  const [detail, setDetail]   = useState<AuditLog | null>(null);

  function buildParams(f: Filters, pg: number) {
    const p: Record<string, string> = { page: String(pg), page_size: "50" };
    if (f.source_name) p.source_name = f.source_name;
    if (f.username)    p.username    = f.username;
    if (f.vendor)      p.vendor      = f.vendor;
    if (f.rule_name)   p.rule_name   = f.rule_name;
    if (f.from_date)   p.from_date   = new Date(f.from_date).toISOString();
    if (f.to_date)     p.to_date     = new Date(f.to_date).toISOString();
    return new URLSearchParams(p).toString();
  }

  const { data, isLoading, isFetching } = useQuery<PaginatedResponse<AuditLog>>({
    queryKey: ["audit", applied, page],
    queryFn: () =>
      api.get<PaginatedResponse<AuditLog>>(`/audit?${buildParams(applied, page)}`).then(r => r.data),
  });

  function applySearch() { setApplied({ ...filters }); setPage(1); }
  function clearSearch()  { setFilters(EMPTY); setApplied(EMPTY); setPage(1); }
  function setF<K extends keyof Filters>(k: K, v: string) { setFilters(f => ({ ...f, [k]: v })); }

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="text-xl font-bold text-white">Audit Log</h1>
        <p className="text-sm text-slate-500 mt-0.5">All dropped log events with matched rules</p>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Source</label>
            <input className="input" placeholder="Huawei-NCE-FAN" value={filters.source_name}
              onChange={e => setF("source_name", e.target.value)}
              onKeyDown={e => e.key === "Enter" && applySearch()} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Username</label>
            <input className="input" placeholder="backupuser" value={filters.username}
              onChange={e => setF("username", e.target.value)}
              onKeyDown={e => e.key === "Enter" && applySearch()} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Vendor</label>
            <select className="input" value={filters.vendor} onChange={e => setF("vendor", e.target.value)}>
              <option value="">All vendors</option>
              {["Huawei","Nokia","Ericsson"].map(v => <option key={v} value={v.toLowerCase()}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Rule Name</label>
            <input className="input" placeholder="Filter rule name" value={filters.rule_name}
              onChange={e => setF("rule_name", e.target.value)}
              onKeyDown={e => e.key === "Enter" && applySearch()} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">From</label>
            <input className="input" type="datetime-local" value={filters.from_date}
              onChange={e => setF("from_date", e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">To</label>
            <input className="input" type="datetime-local" value={filters.to_date}
              onChange={e => setF("to_date", e.target.value)} />
          </div>
        </div>
        <div className="flex items-center gap-2 mt-4">
          <button onClick={applySearch} className="btn-primary flex items-center gap-2">
            <Search className="w-4 h-4" /> Search
          </button>
          <button onClick={clearSearch} className="btn-secondary flex items-center gap-2">
            <X className="w-4 h-4" /> Clear
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
          <span className="text-sm text-slate-400">
            {isLoading || isFetching ? "Loading..." : `${(data?.total || 0).toLocaleString()} dropped events`}
          </span>
          {data && data.pages > 1 && (
            <div className="flex items-center gap-1">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="btn-secondary py-1 px-2">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs text-slate-400 px-2">{page} / {data.pages}</span>
              <button disabled={page >= data.pages} onClick={() => setPage(p => p + 1)} className="btn-secondary py-1 px-2">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="w-7 h-7 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : !data?.items.length ? (
          <div className="text-center py-12 text-slate-500">
            <FileWarning className="w-8 h-8 mx-auto mb-2 text-slate-700" />
            <p>No audit events found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px]">
              <thead className="bg-slate-800/50">
                <tr>
                  {["Timestamp","Source","Vendor","Username","Reason","Rule Matched","Pattern",""].map(h => (
                    <th key={h} className="th">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map(e => (
                  <tr key={e.id} className="table-row">
                    <td className="td font-mono text-xs text-slate-400 whitespace-nowrap">{fmtDate(e.timestamp)}</td>
                    <td className="td text-xs">{e.source_name || e.source_ip}</td>
                    <td className="td"><span className={vendorClass(e.vendor)}>{e.vendor || "—"}</span></td>
                    <td className="td font-mono text-xs text-red-300">{e.username || "—"}</td>
                    <td className="td text-xs text-slate-400 max-w-[180px] truncate">{e.reason}</td>
                    <td className="td text-xs">
                      {e.rule_name
                        ? <span className="badge-yellow">{e.rule_name}</span>
                        : <span className="text-slate-600">—</span>}
                    </td>
                    <td className="td font-mono text-xs text-slate-400">{e.matched_pattern || "—"}</td>
                    <td className="td">
                      <button onClick={() => setDetail(e)} className="p-1.5 hover:bg-slate-700 rounded text-slate-500 hover:text-white">
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail modal */}
      {detail && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl max-h-[85vh] overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800 sticky top-0 bg-slate-900">
              <h2 className="font-semibold text-white flex items-center gap-2">
                <span className="badge-red">Dropped</span> Audit Event
              </h2>
              <button onClick={() => setDetail(null)} className="text-slate-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="px-6 py-5 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                {[
                  ["Timestamp", fmtDate(detail.timestamp)],
                  ["Source IP", detail.source_ip],
                  ["Source Name", detail.source_name || "—"],
                  ["Vendor", detail.vendor || "—"],
                  ["Username", detail.username || "—"],
                  ["Action", detail.action],
                  ["Reason", detail.reason],
                  ["Rule ID", detail.rule_id || "—"],
                  ["Rule Name", detail.rule_name || "—"],
                  ["Matched Pattern", detail.matched_pattern || "—"],
                ].map(([k, v]) => (
                  <div key={k}>
                    <p className="text-xs text-slate-500 mb-0.5">{k}</p>
                    <p className="text-slate-200 font-mono text-xs break-all">{v}</p>
                  </div>
                ))}
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1.5">Raw Message (not stored/forwarded)</p>
                <pre className="bg-slate-950 border border-slate-800 rounded-lg p-4 text-xs text-slate-300 font-mono whitespace-pre-wrap break-all overflow-auto max-h-40">
                  {detail.raw_message}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
