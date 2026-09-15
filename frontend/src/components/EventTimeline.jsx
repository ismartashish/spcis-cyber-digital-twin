import React, { useState } from 'react';
import { History, CheckCircle2, XCircle, AlertTriangle, Eye, ShieldAlert, Check, Shield } from 'lucide-react';

export default function EventTimeline({ events }) {
  const [filter, setFilter] = useState('all'); // 'all', 'success', 'detected'

  const filteredEvents = (events || []).filter((e) => {
    if (filter === 'success') return e.result === 'SUCCESS';
    if (filter === 'detected') return e.detected;
    return true;
  });

  return (
    <div className="rounded-2xl bg-[#0b1222]/90 border border-slate-800 p-5 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 mb-4 gap-3">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-100 font-mono">
            Incident Event Stream & Causal Timeline
          </h3>
          <span className="text-xs font-mono text-slate-400">
            ({filteredEvents.length} events)
          </span>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setFilter('all')}
            className={`px-2.5 py-1 rounded-lg transition-all ${filter === 'all' ? 'bg-cyan-500/20 text-cyan-300 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('success')}
            className={`px-2.5 py-1 rounded-lg transition-all ${filter === 'success' ? 'bg-emerald-500/20 text-emerald-300 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Successes
          </button>
          <button
            onClick={() => setFilter('detected')}
            className={`px-2.5 py-1 rounded-lg transition-all ${filter === 'detected' ? 'bg-red-500/20 text-red-300 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Detected
          </button>
        </div>
      </div>

      {filteredEvents.length === 0 ? (
        <div className="py-12 text-center text-xs font-mono text-slate-500">
          No events matching criteria yet. Execute simulation steps to generate incident logs.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
          {filteredEvents.map((ev, idx) => {
            const isSuccess = ev.result === 'SUCCESS';
            return (
              <div
                key={idx}
                className={`p-3 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 ${
                  ev.crown_jewel
                    ? 'bg-red-950/40 border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.2)]'
                    : isSuccess
                    ? 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
                    : 'bg-slate-900/40 border-slate-800/60 opacity-75'
                }`}
              >
                {/* Left: Step, Result Icon, Action Name */}
                <div className="flex items-center gap-3">
                  <span className="w-12 text-center py-1 rounded bg-slate-800 text-[11px] font-mono text-slate-300 font-bold border border-slate-700/80">
                    STEP {ev.step}
                  </span>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-100 flex items-center gap-1.5">
                        {ev.action}
                      </span>
                      {ev.crown_jewel && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-red-900 border border-red-700 text-red-200 font-mono font-bold animate-pulse">
                          CROWN JEWEL
                        </span>
                      )}
                    </div>
                    {ev.details && (
                      <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                        {ev.details}
                      </p>
                    )}
                  </div>
                </div>

                {/* Right: Badges */}
                <div className="flex items-center gap-2.5 flex-wrap sm:flex-nowrap">
                  {/* Detected badge */}
                  {ev.detected ? (
                    <span className="px-2 py-0.5 rounded bg-red-500/20 border border-red-500/40 text-red-300 text-[10px] font-mono flex items-center gap-1">
                      <Eye className="w-3 h-3" /> DETECTED
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] font-mono">
                      STEALTH
                    </span>
                  )}

                  {/* Reward */}
                  <span className={`px-2 py-0.5 rounded font-mono text-xs font-bold ${
                    ev.reward > 0 ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {ev.reward > 0 ? `+${ev.reward.toFixed(1)}` : ev.reward.toFixed(1)}
                  </span>

                  {/* Result status */}
                  <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold flex items-center gap-1 ${
                    isSuccess ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {isSuccess ? <CheckCircle2 className="w-3 h-3 text-emerald-400" /> : <XCircle className="w-3 h-3 text-slate-500" />}
                    {ev.result}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
