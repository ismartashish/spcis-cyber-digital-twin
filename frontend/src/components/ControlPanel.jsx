import React, { useState } from 'react';
import { Play, SkipForward, RefreshCw, Zap, Sliders, Shield, Cpu, RotateCcw, Flame } from 'lucide-react';

export default function ControlPanel({
  onStep,
  onAutoStep,
  onReset,
  isStepping,
  policyMode,
  setPolicyMode,
  modelLoaded,
  isDone,
  seed,
  setSeed,
}) {
  const [autoSteps, setAutoSteps] = useState(5);

  const handleRandomSeed = () => {
    const newSeed = Math.floor(Math.random() * 1000000);
    setSeed(newSeed);
    onReset(newSeed, policyMode);
  };

  return (
    <div className="rounded-2xl bg-[#0b1222]/90 border border-slate-800 p-5 shadow-xl">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200 font-mono flex items-center gap-2">
          <Sliders className="w-4 h-4 text-cyan-400" />
          Simulation Control Center
        </h2>
        <span className={`text-[11px] font-mono px-2 py-0.5 rounded border ${
          isDone ? 'bg-red-950/40 text-red-400 border-red-500/40' : 'bg-emerald-950/40 text-emerald-400 border-emerald-500/40'
        }`}>
          {isDone ? 'EPISODE FINISHED' : 'READY / ACTIVE'}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Step Action Button */}
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1.5">Single Step</label>
          <button
            onClick={onStep}
            disabled={isStepping || isDone}
            className="w-full h-11 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-xs font-mono shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Zap className={`w-4 h-4 ${isStepping ? 'animate-spin' : ''}`} />
            <span>{isStepping ? 'SIMULATING...' : 'EXECUTE AI STEP'}</span>
          </button>
        </div>

        {/* Auto Run with Step Selector */}
        <div>
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1.5">
            <span>Auto Run</span>
            <span className="text-cyan-400 font-bold">{autoSteps} steps</span>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="range"
              min="1"
              max="20"
              value={autoSteps}
              onChange={(e) => setAutoSteps(parseInt(e.target.value))}
              disabled={isStepping || isDone}
              className="w-full accent-cyan-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
            />
            <button
              onClick={() => onAutoStep(autoSteps)}
              disabled={isStepping || isDone}
              className="h-11 px-4 flex items-center justify-center gap-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-mono transition-all disabled:opacity-40"
            >
              <Play className="w-3.5 h-3.5 text-cyan-400 fill-cyan-400" />
              <span>RUN</span>
            </button>
          </div>
        </div>

        {/* Policy Mode Selector */}
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1.5">Red Agent Policy</label>
          <div className="grid grid-cols-2 gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setPolicyMode('ppo')}
              disabled={!modelLoaded}
              className={`py-1.5 px-2 rounded-lg text-xs font-mono transition-all flex items-center justify-center gap-1.5 ${
                policyMode === 'ppo'
                  ? 'bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              } ${!modelLoaded ? 'opacity-40 cursor-not-allowed' : ''}`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>PPO (RL)</span>
            </button>
            <button
              onClick={() => setPolicyMode('heuristic')}
              className={`py-1.5 px-2 rounded-lg text-xs font-mono transition-all flex items-center justify-center gap-1.5 ${
                policyMode === 'heuristic'
                  ? 'bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Flame className="w-3.5 h-3.5 text-amber-400" />
              <span>Heuristic</span>
            </button>
          </div>
        </div>

        {/* Seed & Reset */}
        <div>
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1.5">
            <span>Deterministic Seed</span>
            <button
              onClick={handleRandomSeed}
              className="text-[10px] text-cyan-400 hover:underline flex items-center gap-0.5"
            >
              <RefreshCw className="w-2.5 h-2.5" /> Randomize
            </button>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(parseInt(e.target.value) || 0)}
              className="w-full h-11 px-3 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
            <button
              onClick={() => onReset(seed, policyMode)}
              className="h-11 px-3.5 flex items-center justify-center gap-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-mono transition-all"
              title="Reset simulation with current seed"
            >
              <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
