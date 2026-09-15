import React, { useState } from 'react';
import { X, Play, BarChart2, Shield, Crosshair, Award, CheckCircle2, AlertTriangle } from 'lucide-react';
import { api } from '../api';

export default function ArenaBenchmark({ onClose, modelLoaded }) {
  const [episodes, setEpisodes] = useState(5);
  const [redPolicy, setRedPolicy] = useState('heuristic');
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const data = await api.runBenchmark(episodes, redPolicy);
      setResults(data);
    } catch (err) {
      setError(err.message || 'Benchmark run failed');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="w-full max-w-3xl max-h-[90vh] bg-[#0b1222] border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <BarChart2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold font-mono text-slate-100">
                Arena Self-Play League Benchmark
              </h2>
              <p className="text-xs text-slate-400">
                Adversarial co-evolution tournament: evaluate red breach rate vs blue containment rate
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Controls Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800">
            {/* Number of episodes */}
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                Batch Episodes
              </label>
              <select
                value={episodes}
                onChange={(e) => setEpisodes(parseInt(e.target.value))}
                disabled={isRunning}
                className="w-full h-10 px-3 rounded-lg bg-slate-800 border border-slate-700 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value={3}>3 Episodes (Fast)</option>
                <option value={5}>5 Episodes (Standard)</option>
                <option value={10}>10 Episodes (Thorough)</option>
                <option value={20}>20 Episodes (Deep League)</option>
              </select>
            </div>

            {/* Red Policy */}
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                Red Policy
              </label>
              <select
                value={redPolicy}
                onChange={(e) => setRedPolicy(e.target.value)}
                disabled={isRunning}
                className="w-full h-10 px-3 rounded-lg bg-slate-800 border border-slate-700 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value="heuristic">Heuristic Baseline Red</option>
                <option value="ppo" disabled={!modelLoaded}>
                  Trained Maskable PPO {modelLoaded ? '' : '(No red_ppo.zip)'}
                </option>
              </select>
            </div>

            {/* Trigger Button */}
            <div className="flex items-end">
              <button
                onClick={handleRun}
                disabled={isRunning}
                className="w-full h-10 flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-mono text-xs font-semibold shadow-lg transition-all disabled:opacity-50"
              >
                <Play className={`w-3.5 h-3.5 fill-white ${isRunning ? 'animate-spin' : ''}`} />
                <span>{isRunning ? 'RUNNING BATCH...' : 'START TOURNAMENT'}</span>
              </button>
            </div>
          </div>

          {error && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs font-mono">
              Error: {error}
            </div>
          )}

          {/* Results Display */}
          {results && (
            <div className="space-y-5">
              <h3 className="text-xs uppercase tracking-wider text-slate-400 font-mono font-bold">
                Tournament Summary Results
              </h3>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {/* Crown Jewel Breach Rate */}
                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] uppercase font-mono text-slate-400">Breach Rate</span>
                  <p className="text-xl font-bold font-mono text-red-400 mt-1">
                    {(results.crown_jewel_compromise_rate * 100).toFixed(1)}%
                  </p>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {results.crown_jewel_compromised_count} of {results.n_episodes} breached
                  </span>
                </div>

                {/* Blue Containment Rate */}
                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] uppercase font-mono text-slate-400">Containment</span>
                  <p className="text-xl font-bold font-mono text-emerald-400 mt-1">
                    {(results.blue_containment_rate * 100).toFixed(1)}%
                  </p>
                  <span className="text-[10px] text-slate-500 font-mono">
                    Defended successfully
                  </span>
                </div>

                {/* Avg Steps */}
                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] uppercase font-mono text-slate-400">Avg Episode Steps</span>
                  <p className="text-xl font-bold font-mono text-cyan-400 mt-1">
                    {results.avg_steps}
                  </p>
                  <span className="text-[10px] text-slate-500 font-mono">
                    Steps to resolution
                  </span>
                </div>

                {/* Avg Red Reward */}
                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] uppercase font-mono text-slate-400">Avg Red Reward</span>
                  <p className="text-xl font-bold font-mono text-amber-400 mt-1">
                    {results.avg_red_reward}
                  </p>
                  <span className="text-[10px] text-slate-500 font-mono">
                    Blue avg: {results.avg_blue_reward}
                  </span>
                </div>
              </div>

              {/* Episode Table */}
              <div className="rounded-xl border border-slate-800 overflow-hidden">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="p-3">Episode</th>
                      <th className="p-3">Outcome</th>
                      <th className="p-3">Steps</th>
                      <th className="p-3">Red Reward</th>
                      <th className="p-3">Blue Reward</th>
                      <th className="p-3">Compromised Nodes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/40 text-slate-300">
                    {results.episodes?.map((ep, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40">
                        <td className="p-3 text-cyan-400 font-semibold">#{idx + 1}</td>
                        <td className="p-3">
                          {ep.crown_jewel_compromised ? (
                            <span className="text-red-400 font-bold flex items-center gap-1">
                              🔴 BREACHED
                            </span>
                          ) : (
                            <span className="text-emerald-400 font-bold flex items-center gap-1">
                              🔵 HELD
                            </span>
                          )}
                        </td>
                        <td className="p-3">{ep.steps_taken}</td>
                        <td className="p-3 text-amber-400">{ep.red_reward.toFixed(2)}</td>
                        <td className="p-3 text-blue-400">{ep.blue_reward.toFixed(2)}</td>
                        <td className="p-3 text-slate-400">{ep.compromised_nodes?.join(', ') || 'None'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
