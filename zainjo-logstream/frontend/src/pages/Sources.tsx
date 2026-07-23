import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../api/client";
import type { LogSource, LogSourceCreate } from "../api/types";
import { fmtDate } from "../utils/format";
import { Plus, Pencil, Trash2, X, Server } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

const VENDORS = ["Huawei", "Nokia", "Ericsson"];
const SYSTEM_TYPES: Record<string, string[]> = {
  Huawei: ["NCE", "U2020", "NetEco", "PRS", "TACACS", "Other"],
  Nokia: ["NetAct", "Manta Ray", "Other"],
  Ericsson: ["ENM", "cENM", "Other"],
};

const EMPTY: LogSourceCreate = {
  name: "", ip_address: "", vendor: "Huawei", system_type: "NCE",
  protocol: "UDP", port: 1514, description: "", enabled: true,
};

export default function Sources() {
  const qc = useQueryClient();
  const { isAdmin } = useAuth();
  const [modal, setModal] = useState<"create" | "edit" | null>(null);
  const [editing, setEditing] = useState<LogSource | null>(null);
  const [form, setForm] = useState<LogSourceCreate>(EMPTY);

  const { data, isLoading } = useQuery({
    queryKey: ["sources"],
    queryFn: () => api.get<{ items: LogSource[]; total: number }>("/sources?page_size=200").then(r => r.data),
  });

  const createMut = useMutation({
    mutationFn: (body: LogSourceCreate) => api.post("/sources", body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["sources"] }); closeModal(); },
  });

  const updateMut = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Partial<LogSourceCreate> }) =>
      api.patch(`/sources/${id}`, body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["sources"] }); closeModal(); },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.delete(`/sources/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });

  function openCreate() { setForm(EMPTY); setEditing(null); setModal("create"); }
  function openEdit(s: LogSource) {
    setForm({ name: s.name, ip_address: s.ip_address, vendor: s.vendor, system_type: s.system_type,
              protocol: s.protocol, port: s.port, description: s.description || "", enabled: s.enabled });
    setEditing(s); setModal("edit");
  }
  function closeModal() { setModal(null); setEditing(null); }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (modal === "create") createMut.mutate(form);
    else if (editing) updateMut.mutate({ id: editing.id, body: form });
  }

  function setField<K extends keyof LogSourceCreate>(k: K, v: LogSourceCreate[K]) {
    setForm(f => ({ ...f, [k]: v }));
  }

  const sources = data?.items || [];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-white">Source Management</h1>
          <p className="text-sm text-slate-500 mt-0.5">{data?.total || 0} sources registered</p>
        </div>
        {isAdmin && (
          <button onClick={openCreate} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Add Source
          </button>
        )}
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <div className="w-7 h-7 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : sources.length === 0 ? (
        <div className="card text-center py-16">
          <Server className="w-10 h-10 text-slate-700 mx-auto mb-3" />
          <p className="text-slate-400 font-medium">No sources configured</p>
          <p className="text-slate-600 text-sm mt-1">Add a syslog source to start collecting logs</p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-800/50 border-b border-slate-800">
              <tr>
                {["Name","IP Address","Vendor","System","Protocol","Port","Status","Updated",""].map(h => (
                  <th key={h} className="th">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sources.map(s => (
                <tr key={s.id} className="table-row">
                  <td className="td font-medium text-slate-100">{s.name}</td>
                  <td className="td font-mono text-slate-400">{s.ip_address}</td>
                  <td className="td">
                    <span className={
                      s.vendor.toLowerCase() === "huawei" ? "badge-red" :
                      s.vendor.toLowerCase() === "nokia" ? "badge-blue" : "badge-purple"
                    }>{s.vendor}</span>
                  </td>
                  <td className="td text-slate-400">{s.system_type}</td>
                  <td className="td">
                    <span className="badge-gray">{s.protocol}</span>
                  </td>
                  <td className="td font-mono">{s.port}</td>
                  <td className="td">
                    {s.enabled
                      ? <span className="badge-green">Active</span>
                      : <span className="badge-red">Disabled</span>}
                  </td>
                  <td className="td text-slate-500 text-xs">{fmtDate(s.updated_at)}</td>
                  <td className="td">
                    {isAdmin && (
                      <div className="flex items-center gap-1">
                        <button onClick={() => openEdit(s)} className="p-1.5 hover:bg-slate-700 rounded text-slate-400 hover:text-white">
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => { if (confirm(`Delete "${s.name}"?`)) deleteMut.mutate(s.id); }}
                          className="p-1.5 hover:bg-red-900/30 rounded text-slate-400 hover:text-red-400"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {modal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl">
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800">
              <h2 className="font-semibold text-white">{modal === "create" ? "Add Source" : "Edit Source"}</h2>
              <button onClick={closeModal} className="text-slate-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Source Name *</label>
                  <input className="input" placeholder="Huawei-NCE-FAN" required
                    value={form.name} onChange={e => setField("name", e.target.value)} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">IP Address *</label>
                  <input className="input" placeholder="10.x.x.x" required
                    value={form.ip_address} onChange={e => setField("ip_address", e.target.value)} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Vendor *</label>
                  <select className="input" value={form.vendor}
                    onChange={e => { setField("vendor", e.target.value); setField("system_type", SYSTEM_TYPES[e.target.value]?.[0] || ""); }}>
                    {VENDORS.map(v => <option key={v}>{v}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">System Type *</label>
                  <select className="input" value={form.system_type} onChange={e => setField("system_type", e.target.value)}>
                    {(SYSTEM_TYPES[form.vendor] || ["Other"]).map(t => <option key={t}>{t}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Protocol</label>
                  <select className="input" value={form.protocol} onChange={e => setField("protocol", e.target.value)}>
                    {["UDP","TCP","BOTH"].map(p => <option key={p}>{p}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Port</label>
                  <input className="input" type="number" min={1} max={65535}
                    value={form.port} onChange={e => setField("port", Number(e.target.value))} />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Description</label>
                <input className="input" placeholder="Optional description"
                  value={form.description} onChange={e => setField("description", e.target.value)} />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="rounded" checked={form.enabled}
                  onChange={e => setField("enabled", e.target.checked)} />
                <span className="text-sm text-slate-300">Enabled</span>
              </label>
              <div className="flex items-center gap-3 pt-2">
                <button type="submit" className="btn-primary">
                  {modal === "create" ? "Add Source" : "Save Changes"}
                </button>
                <button type="button" onClick={closeModal} className="btn-secondary">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
