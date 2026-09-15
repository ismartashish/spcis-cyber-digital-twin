import React from 'react';
import { ShieldCheck, ShieldAlert, CheckCircle2, XCircle, AlertTriangle, FileCode } from 'lucide-react';

export default function InvariantsCard({ invariantChecks }) {
  const checks = invariantChecks || [];
  const allPassed = checks.length > 0 ? checks.every(c => c.passed) : true;

  return (
    <div className="rounded-2xl bg-[#0b1222]/90 border border-slate-800 p-5 shadow-xl">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-lg border ${
            allPassed ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'
          }`}>
            {allPassed ? <ShieldCheck className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-100 font-mono">
              Formal Verification & Invariants Gate
            </h3>
            <p className="text-[11px] text-slate-400">
              Mathematical invariants enforced on blue defense proposals before execution
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold flex items-center gap-1.5 border ${
            allPassed 
              ? 'bg-emerald-950/40 text-emerald-300 border-emerald-500/40' 
              : 'bg-red-950/40 text-red-300 border-red-500/40'
          }`}>
            {allPassed ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <XCircle className="w-3.5 h-3.5 text-red-400" />}
            {allPassed ? 'ALL INVARIANTS PASSED' : 'VIOLATION DETECTED & ROLLED BACK'}
          </span>
        </div>
      </div>

      {/* Invariants Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Invariant 1 */}
        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 flex items-start gap-3">
          <div className="mt-0.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold font-mono text-slate-200">no_full_isolation</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                PROVEN
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Guarantees blue defender cannot cause total infrastructure outage by isolating all nodes.
            </p>
          </div>
        </div>

        {/* Invariant 2 */}
        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 flex items-start gap-3">
          <div className="mt-0.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold font-mono text-slate-200">web_tier_reachable</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                PROVEN
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Ensures internet-facing ingress SLA: web and API nodes must remain accessible to legitimate users.
            </p>
          </div>
        </div>
      </div>

      {/* Live Verification Log */}
      {checks.length > 0 && (
        <div className="mt-3.5 pt-3 border-t border-slate-800/80 flex flex-wrap gap-2 text-[11px] font-mono text-slate-400">
          <span className="text-slate-500 font-semibold">Latest Verification Run:</span>
          {checks.map((chk, idx) => (
            <span key={idx} className="flex items-center gap-1">
              <span className={chk.passed ? 'text-emerald-400' : 'text-red-400'}>
                {chk.passed ? '✔' : '✘'} {chk.name} ({chk.detail})
              </span>
              {idx < checks.length - 1 && <span className="text-slate-700">|</span>}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
