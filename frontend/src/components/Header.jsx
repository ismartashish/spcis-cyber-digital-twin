import React from 'react';
import { Shield, ShieldAlert, Cpu, Terminal, RefreshCw, BarChart2, FileText, Zap, Award } from 'lucide-react';

export default function Header({ state, onReset, onOpenBenchmark, onOpenReport, isConnected }) {
  const kpis = state?.kpis || {};
  const session = state?.session || {};
  const isCompromised = kpis?.crown_jewel_compromised;

  return (
    <header className="border-b border-slate-800 bg-[#0b1120]/90 backdrop-blur-md sticky top-0 z-30 px-6 py-3.5">
      <div className="max-w-[1700px] mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left: Brand & Identity */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
              <Shield className="w-5 h-5" />
            </div>
            <span className="absolute -bottom-1 -right-1 flex h-3 w-3">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isConnected ? 'bg-emerald-400' : 'bg-red-400'}`}></span>
              <span className={`relative inline-flex rounded-full h-3 w-3 ${isConnected ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-wider text-slate-100 font-mono flex items-center gap-1.5">
                SPCIS <span className="text-cyan-400 font-normal text-xs px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/60">DIGITAL TWIN</span>
              </h1>
              <span className="text-xs text-slate-400 hidden sm:inline">•</span>
              <span className="text-xs text-slate-400 font-mono hidden sm:inline">Autonomous Cyber Immune System</span>
            </div>
            <p className="text-xs text-slate-400">Continuous Red-vs-Blue Co-Evolution with Formal Invariant Verification</p>
          </div>
        </div>

        {/* Center: Live Status Indicators */}
        <div className="flex items-center flex-wrap gap-2 sm:gap-3">
          {/* Crown Jewel Status */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-mono transition-all ${
            isCompromised 
              ? 'bg-red-950/40 border-red-500/50 text-red-300 shadow-[0_0_15px_rgba(239,68,68,0.3)] animate-pulse' 
              : 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
          }`}>
            {isCompromised ? <ShieldAlert className="w-4 h-4 text-red-400" /> : <Award className="w-4 h-4 text-emerald-400" />}
            <span>CROWN JEWEL: <strong>{isCompromised ? 'COMPROMISED' : 'SECURE'}</strong></span>
          </div>

          {/* Model Mode */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs font-mono text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>AGENT: <strong className="text-cyan-300">{session.model_loaded ? 'Maskable PPO' : 'Heuristic Red'}</strong></span>
          </div>

          {/* Step & Reward */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs font-mono text-slate-300">
            <span>STEP: <strong className="text-blue-400">{kpis.step || 0}</strong>/40</span>
            <span className="text-slate-600">|</span>
            <span>REWARD: <strong className={kpis.episode_reward >= 0 ? 'text-amber-400' : 'text-slate-400'}>
              {kpis.episode_reward != null ? kpis.episode_reward.toFixed(2) : '0.00'}
            </strong></span>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={onOpenBenchmark}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium transition-all hover:border-slate-500"
            title="Run multi-episode Arena benchmark"
          >
            <BarChart2 className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Arena League</span>
          </button>

          <button
            onClick={onOpenReport}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium transition-all hover:border-slate-500"
            title="Generate & view incident narrative report"
          >
            <FileText className="w-3.5 h-3.5 text-amber-400" />
            <span className="hidden sm:inline">Report</span>
          </button>

          <button
            onClick={onReset}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950/40 hover:bg-cyan-900/60 border border-cyan-600/40 text-cyan-300 text-xs font-medium transition-all hover:border-cyan-400"
            title="Reset simulation episode"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>
      </div>
    </header>
  );
}
