import React from 'react';
import { Shield, ShieldAlert, Crosshair, Cpu, Eye, Lock, Wrench, AlertOctagon, TrendingUp, Zap } from 'lucide-react';

export default function AgentTelemetry({ state }) {
  const kpis = state?.kpis || {};
  const session = state?.session || {};

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      {/* Red Agent Panel */}
      <div className="rounded-2xl bg-[#0e1424]/90 border border-red-950/60 p-5 shadow-xl relative overflow-hidden">
        {/* Glow Header */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-600 to-rose-400"></div>

        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400">
              <Crosshair className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
                RED ADVERSARY AGENT
                <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-red-950 border border-red-800 text-red-300">
                  {session.policy_mode === 'ppo' ? 'Maskable PPO' : 'Heuristic Red'}
                </span>
              </h3>
              <p className="text-[11px] text-slate-400">Tactics: Scan, Exploit, Pivot, Crown Jewel Exfil</p>
            </div>
          </div>
          <div className="text-right font-mono">
            <span className="text-[10px] text-slate-400 block">STEP REWARD</span>
            <span className={`text-sm font-bold ${session.last_reward >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {session.last_reward != null ? `${session.last_reward > 0 ? '+' : ''}${session.last_reward.toFixed(2)}` : '0.00'}
            </span>
          </div>
        </div>

        {/* Current / Last Action Banner */}
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 mb-4">
          <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block mb-1">
            Last Executed Action
          </span>
          <p className="text-xs font-mono font-bold text-red-300 break-all">
            {session.last_action || 'Standing by...'}
          </p>
        </div>

        {/* Tactical Metrics Grid */}
        <div className="grid grid-cols-3 gap-3">
          {/* Exploits */}
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
              <span>EXPLOIT RATE</span>
              <span className="text-red-400 font-bold">{kpis.exploit_rate || 0}%</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mb-2">
              <div
                className="bg-red-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, kpis.exploit_rate || 0)}%` }}
              ></div>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              {kpis.total_exploits || 0} attempts
            </span>
          </div>

          {/* Pivots */}
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
              <span>PIVOT RATE</span>
              <span className="text-amber-400 font-bold">{kpis.pivot_rate || 0}%</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mb-2">
              <div
                className="bg-amber-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, kpis.pivot_rate || 0)}%` }}
              ></div>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              {kpis.total_pivots || 0} attempts
            </span>
          </div>

          {/* Scans */}
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
              <span>SCAN RATE</span>
              <span className="text-cyan-400 font-bold">{kpis.scan_rate || 0}%</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mb-2">
              <div
                className="bg-cyan-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, kpis.scan_rate || 0)}%` }}
              ></div>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              {kpis.total_scans || 0} attempts
            </span>
          </div>
        </div>
      </div>

      {/* Blue Defender Panel */}
      <div className="rounded-2xl bg-[#0e1424]/90 border border-cyan-950/60 p-5 shadow-xl relative overflow-hidden">
        {/* Glow Header */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 to-blue-500"></div>

        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
                BLUE IMMUNE DEFENDER
                <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">
                  Adaptive Response
                </span>
              </h3>
              <p className="text-[11px] text-slate-400">Sensors: Detection, Node Isolation, CVE Patching</p>
            </div>
          </div>
          <div className="text-right font-mono">
            <span className="text-[10px] text-slate-400 block">TOTAL DETECTIONS</span>
            <span className="text-sm font-bold text-cyan-400">
              {kpis.blue_detections || 0}
            </span>
          </div>
        </div>

        {/* Blue Strategy Description */}
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 mb-4 flex items-center justify-between text-xs font-mono">
          <span className="text-slate-400 flex items-center gap-2">
            <Eye className="w-4 h-4 text-cyan-400" />
            Real-time Anomaly Thresholding & Invariant Gate
          </span>
          <span className="text-emerald-400 font-bold">ACTIVE</span>
        </div>

        {/* Blue Counters Grid */}
        <div className="grid grid-cols-3 gap-3">
          {/* Isolations */}
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="flex items-center gap-2 text-slate-400 text-xs font-mono mb-1">
              <Lock className="w-3.5 h-3.5 text-amber-400" />
              <span>ISOLATIONS</span>
            </div>
            <p className="text-lg font-bold font-mono text-slate-100">
              {kpis.blue_isolations || 0}
            </p>
            <span className="text-[10px] text-slate-500 font-mono">Node quarantines</span>
          </div>

          {/* Patches */}
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="flex items-center gap-2 text-slate-400 text-xs font-mono mb-1">
              <Wrench className="w-3.5 h-3.5 text-emerald-400" />
              <span>PATCHES</span>
            </div>
            <p className="text-lg font-bold font-mono text-slate-100">
              {kpis.blue_patches || 0}
            </p>
            <span className="text-[10px] text-slate-500 font-mono">CVEs remediated</span>
          </div>

          {/* Invariant Violations */}
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="flex items-center gap-2 text-slate-400 text-xs font-mono mb-1">
              <AlertOctagon className="w-3.5 h-3.5 text-red-400" />
              <span>ROLLBACKS</span>
            </div>
            <p className="text-lg font-bold font-mono text-slate-100">
              {kpis.blue_violations || 0}
            </p>
            <span className="text-[10px] text-slate-500 font-mono">Safety gated</span>
          </div>
        </div>
      </div>
    </div>
  );
}
