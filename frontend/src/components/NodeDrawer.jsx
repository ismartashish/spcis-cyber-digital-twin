import React from 'react';
import { X, ShieldAlert, ShieldCheck, Bug, Lock, ArrowRight, Activity, Terminal } from 'lucide-react';

export default function NodeDrawer({ node, onClose }) {
  if (!node) return null;

  const vulns = node.vulnerabilities || [];
  const unpatchedCount = vulns.filter(v => !v.patched).length;

  const getSeverityBadge = (severity) => {
    if (severity >= 9.0) return 'bg-red-500/20 text-red-400 border-red-500/40';
    if (severity >= 7.0) return 'bg-orange-500/20 text-orange-400 border-orange-500/40';
    if (severity >= 4.0) return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
    return 'bg-blue-500/20 text-blue-400 border-blue-500/40';
  };

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-full sm:w-[460px] bg-[#0b1222] border-l border-slate-800 shadow-2xl p-6 overflow-y-auto transform transition-transform duration-300">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-xl border ${
            node.compromised 
              ? 'bg-red-950/40 border-red-500/40 text-red-400' 
              : node.isolated 
              ? 'bg-amber-950/40 border-amber-500/40 text-amber-400' 
              : 'bg-cyan-950/40 border-cyan-500/40 text-cyan-400'
          }`}>
            <Bug className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold font-mono text-slate-100 flex items-center gap-2">
              {node.id}
              {node.is_crown_jewel && (
                <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/40 text-amber-300">
                  CROWN JEWEL
                </span>
              )}
            </h2>
            <p className="text-xs text-slate-400 font-mono">Role: {node.role.toUpperCase()}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Node Status Overview */}
      <div className="mt-5 grid grid-cols-2 gap-3">
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Status</span>
          <p className={`text-sm font-bold font-mono mt-0.5 ${
            node.compromised ? 'text-red-400' : node.isolated ? 'text-amber-400' : 'text-emerald-400'
          }`}>
            {node.status}
          </p>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Detection Sensor</span>
          <p className="text-sm font-bold font-mono text-cyan-400 mt-0.5">
            {((node.detection_sensitivity || 0.3) * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Reachability & Network Topology */}
      <div className="mt-5 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono mb-2 flex items-center gap-1.5">
          <ArrowRight className="w-3.5 h-3.5 text-blue-400" />
          Ingress Reachability
        </h3>
        {node.reachable_from && node.reachable_from.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {node.reachable_from.map((src) => (
              <span
                key={src}
                className="px-2.5 py-1 rounded bg-slate-800 text-xs font-mono text-slate-300 border border-slate-700"
              >
                from <strong className="text-cyan-400">{src}</strong>
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-cyan-400/90 font-mono">
            Internet-Facing (Perimeter Gateway — No prerequisite nodes required)
          </p>
        )}
      </div>

      {/* Vulnerabilities & CVEs */}
      <div className="mt-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
            <Bug className="w-3.5 h-3.5 text-red-400" />
            Attack Surface Vulnerabilities ({vulns.length})
          </h3>
          <span className="text-xs font-mono text-slate-400">
            {unpatchedCount} unpatched
          </span>
        </div>

        {vulns.length === 0 ? (
          <p className="text-xs text-slate-400 p-4 bg-slate-900/60 rounded-xl border border-slate-800">
            No known CVEs registered on this node.
          </p>
        ) : (
          <div className="space-y-2.5">
            {vulns.map((vuln) => (
              <div
                key={vuln.vuln_id}
                className={`p-3.5 rounded-xl border transition-all ${
                  vuln.patched
                    ? 'bg-slate-900/40 border-slate-800 opacity-60'
                    : 'bg-slate-900/90 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-slate-200">
                    {vuln.vuln_id}
                  </span>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getSeverityBadge(vuln.severity)}`}>
                    CVSS {vuln.severity.toFixed(1)}
                  </span>
                </div>

                <div className="mt-2 flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>Class: <strong className="text-slate-300">{vuln.vuln_class}</strong></span>
                  <span>Exploit Prob: <strong className="text-cyan-400">{(vuln.exploitability * 100).toFixed(0)}%</strong></span>
                </div>

                {/* Exploitability Bar */}
                <div className="mt-2 w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${vuln.patched ? 'bg-emerald-500' : 'bg-red-500'}`}
                    style={{ width: `${vuln.exploitability * 100}%` }}
                  ></div>
                </div>

                <div className="mt-2 flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-400">State:</span>
                  {vuln.patched ? (
                    <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                      <ShieldCheck className="w-3.5 h-3.5" /> PATCHED
                    </span>
                  ) : (
                    <span className="text-red-400 flex items-center gap-1 font-semibold">
                      <ShieldAlert className="w-3.5 h-3.5" /> EXPLOITABLE
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="mt-6 pt-4 border-t border-slate-800 text-[11px] font-mono text-slate-400 leading-relaxed">
        SPCIS formally verifies that any patch or isolation action targeting this node preserves legitimate ingress traffic invariants.
      </div>
    </div>
  );
}
