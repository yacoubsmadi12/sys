import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import type { SyslogEntry, PaginatedResponse } from "../api/types";
import { fmtDate, severityClass, vendorClass } from "../utils/format";
import { Search, ChevronLeft, ChevronRight, X, Eye } from "lucide-react";

const SEVERITIES = ["EMERGENCY","ALERT","CRITICAL","ERROR","WARNING","NOTICE","INFO","DEBUG"];

interface Filters {
  username: string; source_name: string; vendor: string;
  source_ip: string; severity_name: string; keyword: string;
  from_date: string; to_date: string; is_dropped: string;
}

const EMPTY: Filters = {
  username: "", source_name: "", vendor: "", source_ip: "",
  severity_name: "", keyword: "", from_date: "", to_date: "", is_dropped: "",
};

export default function LogSearch() {
  const [filters, setFilters] = useState<Filters>(EMPTY);
  const [applied, setApplied] = useState<Filters>(EMPTY);
  const [page, setPage]       = useState(1);
  const [detail, setDetail]   = useState<SyslogEntry | null>(null);

  function buildParams(f: Filters, pg: number) {
    const p: Record<string, string> = { page: String(pg), page_size: "50" };
    if (f.username)     p.username     = f.username;
    if (f.source_name)  p.source_name  = f.source_name;
    if (f.vendor)       p.vendor       = f.vendor;
    if (f.source_ip)    p.source_ip    = f.source_ip;
    if (f.severity_name) p.severity_name = f.severity_name;
    if (f.keyword)      p.keyword      = f.keyword;
    if (f.from_date)    p.from_date    = new Date(f.from_date).toISOString();
    if (f.to_date)      p.to_date      = new Date(f.to_date).toISOString();
    if (f.is_dropped !== "") p.is_dropped = f.is_dropped;
    return new URLSearchParams(p).toString();
  }

  const { data, isLoading, isFetching } = useQuery<PaginatedResponse<SyslogEntry>>({
    queryKey: ["logs", applied, page],
    queryFn: () =>
      api.get<PaginatedResponse<SyslogEntry>>(`/logs?${buildParams(applied, page)}`).then(r => r.data),
  });

  function applySearch() { setApplied({ ...filters }); setPage(1); }
  function clearSearch()  { setFilters(EMPTY); setApplied(EMPTY); setPage(1); }

  function setF<K extends keyof Filters>(k: K, v: string) {
    setFilters(f => ({ ...f, [k]: v }));
  }

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="text-xl font-bold text-white">Log Search</h1>
        <p className="text-sm text-slate-500 mt-0.5">Search and filter syslog entries</p>
      </div>

      {/* Filter panel */}
      <div className="card">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Username</label>
            <input className="input" placeholder="backupuser" value={filters.username}
              onChange={e => setF("username", e.target.value)}
              onKeyDown={e => e.key === "Enter" && applySearch()} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Source</label>
            <input className="input" placeholder="Huawei-NCE-FAN" value={filters.source_name}
              onChange={e => setF("source_name", e.target.value)}
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
            <label className="block text-xs font-medium text-slate-400 mb-1">Source IP</label>
            <input className="input" placeholder="10.x.x.x" value={filters.source_ip}
              onChange={e => setF("source_ip", e.target.value)}
              onKeyDown={e => e.key === "Enter" && applySearch()} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Severity</label>
            <select className="input" value={filters.severity_name} onChange={e => setF("severity_name", e.target.value)}>
              <option value="">All severities</option>
              {SEVERITIES.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Status</label>
            <select className="input" value={filters.is_dropped} onChange={e => setF("is_dropped", e.target.value)}>
              <option value="">All</option>
              <option value="false">Accepted</option>
              <option value="true">Dropped</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">From Date</label>
            <input className="input" type="datetime-local" value={filters.from_date}
              onChange={e => setF("from_date", e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">To Date</label>
            <input className="input" type="datetime-local" value={filters.to_date}
              onChange={e => setF("to_date", e.target.value)} />
          </div>
        </div>
        <div className="mt-3">
          <label className="block text-xs font-medium text-slate-400 mb-1">Keyword (message body)</label>
          <input className="input" placeholder="Search in raw message..." value={filters.keyword}
            onChange={e => setF("keyword", e.target.value)}
            onKeyDown={e => e.key === "Enter" && applySearch()} />
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

      {/* Results */}
      <div className="card p-0 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
          <span className="text-sm text-slate-400">
            {isLoading || isFetching
              ? "Loading..."
              : `${(data?.total || 0).toLocaleString()} results`}
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
            <Search className="w-8 h-8 mx-auto mb-2 text-slate-700" />
            <p>No results found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px]">
              <thead className="bg-slate-800/50">
                <tr>
                  {["Time","Source","Vendor","Username","Severity","Status","Message",""].map(h => (
                    <th key={h} className="th">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map(e => (
                  <tr key={e.id} className="table-row">
                    <td className="td font-mono text-xs text-slate-400 whitespace-nowrap">{fmtDate(e.received_at)}</td>
                    <td className="td text-xs whitespace-nowrap">{e.source_name || e.source_ip}</td>
                    <td className="td"><span className={vendorClass(e.vendor)}>{e.vendor || "—"}</span></td>
                    <td className="td font-mono text-xs">{e.username || "—"}</td>
                    <td className="td"><span className={severityClass(e.severity_name)}>{e.severity_name || "—"}</span></td>
                    <td className="td">
                      {e.is_dropped
                        ? <span className="badge-red">Dropped</span>
                        : <span className="badge-green">OK</span>}
                    </td>
                    <td className="td text-xs text-slate-400 max-w-xs truncate">
                      {(e.message || e.raw_message).slice(0, 100)}
                    </td>
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
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800 sticky top-0 bg-slate-900">
              <h2 className="font-semibold text-white">Log Entry Detail</h2>
              <button onClick={() => setDetail(null)} className="text-slate-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="px-6 py-5 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                {[
                  ["Received", fmtDate(detail.received_at)],
                  ["Log Timestamp", fmtDate(detail.log_timestamp)],
                  ["Source IP", detail.source_ip],
                  ["Source Name", detail.source_name || "—"],
                  ["Vendor", detail.vendor || "—"],
                  ["Hostname", detail.hostname || "—"],
                  ["App Name", detail.app_name || "—"],
                  ["Username", detail.username || "—"],
                  ["Severity", detail.severity_name || "—"],
                  ["Status", detail.is_dropped ? "Dropped" : "Accepted"],
                  ["Drop Reason", detail.drop_reason || "—"],
                  ["Forwarded to SIEM", detail.forwarded_to_siem ? "Yes" : "No"],
                ].map(([k, v]) => (
                  <div key={k}>
                    <p className="text-xs text-slate-500 mb-0.5">{k}</p>
                    <p className="text-slate-200 font-mono text-xs break-all">{v}</p>
                  </div>
                ))}
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1.5">Raw Message</p>
                <pre className="bg-slate-950 border border-slate-800 rounded-lg p-4 text-xs text-slate-300 font-mono whitespace-pre-wrap break-all overflow-auto max-h-40">
                  {detail.raw_message}
                </pre>
              </div>
              {detail.parsed_fields && Object.keys(detail.parsed_fields).length > 0 && (
                <div>
                  <p className="text-xs text-slate-500 mb-1.5">Parsed Fields</p>
                  <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-1">
                    {Object.entries(detail.parsed_fields).map(([k, v]) => (
                      <div key={k} className="flex gap-3 text-xs">
                        <span className="text-slate-500 w-28 flex-shrink-0">{k}</span>
                        <span className="text-slate-300 font-mono">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
