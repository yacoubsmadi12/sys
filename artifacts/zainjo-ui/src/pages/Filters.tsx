import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../api/client";
import type { FilterRule, FilterRuleCreate, LogSource } from "../api/types";
import { Plus, Trash2, X, Filter, UserX, ChevronDown, ChevronRight } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

const EMPTY_RULE: FilterRuleCreate = {
  name: "", source_id: "", description: "", field: "username",
  pattern_type: "exact", action: "drop", enabled: true, patterns: [],
};

export default function Filters() {
  const qc = useQueryClient();
  const { isAdmin } = useAuth();
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState<FilterRuleCreate>(EMPTY_RULE);
  const [patternInput, setPatternInput] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [newUserInputs, setNewUserInputs] = useState<Record<string, string>>({});

  const { data: sources } = useQuery({
    queryKey: ["sources"],
    queryFn: () => api.get<{ items: LogSource[] }>("/sources?page_size=200").then(r => r.data),
  });

  const { data: rules, isLoading } = useQuery({
    queryKey: ["filters"],
    queryFn: () => api.get<{ items: FilterRule[]; total: number }>("/filters?page_size=200").then(r => r.data),
  });

  const createRule = useMutation({
    mutationFn: (body: FilterRuleCreate) => api.post("/filters", body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["filters"] }); setModal(false); setForm(EMPTY_RULE); },
  });

  const deleteRule = useMutation({
    mutationFn: (id: string) => api.delete(`/filters/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["filters"] }),
  });

  const addUser = useMutation({
    mutationFn: ({ ruleId, pattern }: { ruleId: string; pattern: string }) =>
      api.post(`/filters/${ruleId}/users`, { pattern }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["filters"] }),
  });

  const removeUser = useMutation({
    mutationFn: ({ ruleId, userId }: { ruleId: string; userId: string }) =>
      api.delete(`/filters/${ruleId}/users/${userId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["filters"] }),
  });

  function addPattern() {
    const p = patternInput.trim();
    if (!p || form.patterns.includes(p)) return;
    setForm(f => ({ ...f, patterns: [...f.patterns, p] }));
    setPatternInput("");
  }

  function removePattern(p: string) {
    setForm(f => ({ ...f, patterns: f.patterns.filter(x => x !== p) }));
  }

  function toggleExpand(id: string) {
    setExpanded(s => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });
  }

  function handleAddUserToRule(ruleId: string) {
    const p = (newUserInputs[ruleId] || "").trim();
    if (!p) return;
    addUser.mutate({ ruleId, pattern: p });
    setNewUserInputs(i => ({ ...i, [ruleId]: "" }));
  }

  const sourceMap = Object.fromEntries((sources?.items || []).map(s => [s.id, s.name]));

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-white">Filter Rules</h1>
          <p className="text-sm text-slate-500 mt-0.5">{rules?.total || 0} rules configured</p>
        </div>
        {isAdmin && (
          <button onClick={() => { setForm(EMPTY_RULE); setModal(true); }} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> New Rule
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <div className="w-7 h-7 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : !rules?.items.length ? (
        <div className="card text-center py-16">
          <Filter className="w-10 h-10 text-slate-700 mx-auto mb-3" />
          <p className="text-slate-400 font-medium">No filter rules configured</p>
          <p className="text-slate-600 text-sm mt-1">Create a rule to start blocking users or patterns</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rules.items.map(rule => (
            <div key={rule.id} className="card p-0 overflow-hidden">
              {/* Rule header */}
              <div className="flex items-center gap-3 px-5 py-4 cursor-pointer hover:bg-slate-800/30"
                onClick={() => toggleExpand(rule.id)}>
                {expanded.has(rule.id)
                  ? <ChevronDown className="w-4 h-4 text-slate-500 flex-shrink-0" />
                  : <ChevronRight className="w-4 h-4 text-slate-500 flex-shrink-0" />}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-100">{rule.name}</span>
                    {!rule.enabled && <span className="badge-gray">Disabled</span>}
                    <span className="badge-red">drop</span>
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    Source: <span className="text-slate-400">{sourceMap[rule.source_id] || rule.source_id}</span>
                    {" · "}{rule.field} · {rule.pattern_type}
                    {" · "}<span className="text-slate-400">{rule.blocked_users.length} patterns</span>
                  </div>
                </div>
                {isAdmin && (
                  <button
                    onClick={e => { e.stopPropagation(); if (confirm(`Delete rule "${rule.name}"?`)) deleteRule.mutate(rule.id); }}
                    className="p-1.5 hover:bg-red-900/30 rounded text-slate-500 hover:text-red-400"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Expanded: blocked users */}
              {expanded.has(rule.id) && (
                <div className="border-t border-slate-800 px-5 pb-5 pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                      <UserX className="w-3.5 h-3.5" /> Blocked Patterns
                    </span>
                  </div>
                  <div className="space-y-1.5 mb-4">
                    {rule.blocked_users.length === 0 ? (
                      <p className="text-slate-600 text-sm">No patterns added yet</p>
                    ) : rule.blocked_users.map(bu => (
                      <div key={bu.id} className="flex items-center gap-2 bg-slate-800 rounded-lg px-3 py-2">
                        <span className="font-mono text-sm text-slate-300 flex-1">{bu.pattern}</span>
                        {isAdmin && (
                          <button onClick={() => removeUser.mutate({ ruleId: rule.id, userId: bu.id })}
                            className="text-slate-500 hover:text-red-400 transition-colors">
                            <X className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                  {isAdmin && (
                    <div className="flex gap-2">
                      <input
                        className="input flex-1"
                        placeholder="Username or pattern to block"
                        value={newUserInputs[rule.id] || ""}
                        onChange={e => setNewUserInputs(i => ({ ...i, [rule.id]: e.target.value }))}
                        onKeyDown={e => e.key === "Enter" && handleAddUserToRule(rule.id)}
                      />
                      <button onClick={() => handleAddUserToRule(rule.id)} className="btn-secondary flex-shrink-0">
                        Add
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create modal */}
      {modal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl">
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800">
              <h2 className="font-semibold text-white">New Filter Rule</h2>
              <button onClick={() => setModal(false)} className="text-slate-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={e => { e.preventDefault(); createRule.mutate(form); }} className="px-6 py-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Rule Name *</label>
                <input className="input" placeholder="Block backup users" required
                  value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Source *</label>
                <select className="input" required value={form.source_id}
                  onChange={e => setForm(f => ({ ...f, source_id: e.target.value }))}>
                  <option value="">Select source...</option>
                  {(sources?.items || []).map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Field</label>
                  <select className="input" value={form.field}
                    onChange={e => setForm(f => ({ ...f, field: e.target.value }))}>
                    {["username","hostname","message"].map(f => <option key={f}>{f}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Match Type</label>
                  <select className="input" value={form.pattern_type}
                    onChange={e => setForm(f => ({ ...f, pattern_type: e.target.value }))}>
                    {["exact","contains","regex"].map(t => <option key={t}>{t}</option>)}
                  </select>
                </div>
              </div>

              {/* Patterns */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Initial Blocked Patterns</label>
                <div className="flex gap-2 mb-2">
                  <input className="input flex-1" placeholder="e.g. backupuser"
                    value={patternInput} onChange={e => setPatternInput(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addPattern())} />
                  <button type="button" onClick={addPattern} className="btn-secondary flex-shrink-0">Add</button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {form.patterns.map(p => (
                    <span key={p} className="badge-gray flex items-center gap-1">
                      <span className="font-mono">{p}</span>
                      <button type="button" onClick={() => removePattern(p)}>
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={form.enabled}
                  onChange={e => setForm(f => ({ ...f, enabled: e.target.checked }))} />
                <span className="text-sm text-slate-300">Enabled</span>
              </label>

              <div className="flex items-center gap-3 pt-2">
                <button type="submit" className="btn-primary">Create Rule</button>
                <button type="button" onClick={() => setModal(false)} className="btn-secondary">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
