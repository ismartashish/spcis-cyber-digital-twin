import React from 'react';
import { TrendingUp, Activity, Cpu, Award } from 'lucide-react';

export default function AnalyticsCharts({ rewardHistory, entropyHistory }) {
  const rewards = rewardHistory || [];
  const entropies = entropyHistory || [];

  // Calculate cumulative rewards
  let cum = 0;
  const cumulativeRewards = rewards.map(r => {
    cum += r;
    return cum;
  });

  // SVG Chart Dimensions
  const chartWidth = 500;
  const chartHeight = 160;
  const padding = { top: 20, right: 20, bottom: 25, left: 35 };
  const graphWidth = chartWidth - padding.left - padding.right;
  const graphHeight = chartHeight - padding.top - padding.bottom;

  // Reward points
  const maxReward = Math.max(10, ...cumulativeRewards, ...rewards);
  const minReward = Math.min(-5, ...cumulativeRewards, ...rewards);
  const rewardRange = Math.max(1, maxReward - minReward);

  const getRewardY = (val) => {
    const norm = (val - minReward) / rewardRange;
    return chartHeight - padding.bottom - norm * graphHeight;
  };

  const getRewardX = (idx, total) => {
    if (total <= 1) return padding.left;
    return padding.left + (idx / (total - 1)) * graphWidth;
  };

  // Build SVG paths for Rewards
  const stepRewardPoints = rewards.map((val, idx) => `${getRewardX(idx, rewards.length)},${getRewardY(val)}`).join(' ');
  const cumRewardPoints = cumulativeRewards.map((val, idx) => `${getRewardX(idx, cumulativeRewards.length)},${getRewardY(val)}`).join(' ');

  // Entropy points (0 to 1)
  const getEntropyY = (val) => {
    const clamped = Math.max(0, Math.min(1, val));
    return chartHeight - padding.bottom - clamped * graphHeight;
  };
  const entropyPoints = entropies.map((val, idx) => `${getRewardX(idx, entropies.length)},${getEntropyY(val)}`).join(' ');

  const currentEntropy = entropies.length > 0 ? entropies[entropies.length - 1] : 0;
  const totalEpisodeReward = cumulativeRewards.length > 0 ? cumulativeRewards[cumulativeRewards.length - 1] : 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      {/* Reward Chart */}
      <div className="rounded-2xl bg-[#0b1222]/90 border border-slate-800 p-5 shadow-xl">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold font-mono text-slate-100">
              Red Agent Reward Progression
            </h3>
          </div>
          <div className="flex items-center gap-3 text-xs font-mono">
            <span className="flex items-center gap-1 text-cyan-400">
              <span className="w-2.5 h-0.5 bg-cyan-400"></span> Step
            </span>
            <span className="flex items-center gap-1 text-amber-400">
              <span className="w-2.5 h-0.5 bg-amber-400"></span> Cumulative
            </span>
            <span className="text-slate-200 font-bold px-2 py-0.5 rounded bg-slate-800">
              Total: {totalEpisodeReward.toFixed(2)}
            </span>
          </div>
        </div>

        {rewards.length === 0 ? (
          <div className="h-[160px] flex items-center justify-center text-xs font-mono text-slate-500">
            Awaiting first agent step to plot reward curve...
          </div>
        ) : (
          <div className="w-full overflow-hidden">
            <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full h-[160px]">
              {/* Zero line */}
              {minReward < 0 && maxReward > 0 && (
                <line
                  x1={padding.left}
                  y1={getRewardY(0)}
                  x2={chartWidth - padding.right}
                  y2={getRewardY(0)}
                  stroke="#334155"
                  strokeDasharray="4 4"
                  strokeWidth="1"
                />
              )}

              {/* Step Reward Line */}
              {rewards.length > 1 && (
                <polyline
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="1.5"
                  points={stepRewardPoints}
                  opacity="0.8"
                />
              )}

              {/* Cumulative Reward Line */}
              {cumulativeRewards.length > 1 && (
                <polyline
                  fill="none"
                  stroke="#f59e0b"
                  strokeWidth="2.5"
                  points={cumRewardPoints}
                />
              )}

              {/* Points */}
              {cumulativeRewards.map((val, idx) => (
                <circle
                  key={idx}
                  cx={getRewardX(idx, cumulativeRewards.length)}
                  cy={getRewardY(val)}
                  r="3.5"
                  fill="#f59e0b"
                  stroke="#0b1222"
                  strokeWidth="1.5"
                />
              ))}

              {/* Y Axis Labels */}
              <text x={padding.left - 6} y={padding.top + 5} fill="#64748b" fontSize="9" textAnchor="end" fontFamily="monospace">
                {maxReward.toFixed(0)}
              </text>
              <text x={padding.left - 6} y={chartHeight - padding.bottom} fill="#64748b" fontSize="9" textAnchor="end" fontFamily="monospace">
                {minReward.toFixed(0)}
              </text>
            </svg>
          </div>
        )}
      </div>

      {/* Policy Entropy Chart */}
      <div className="rounded-2xl bg-[#0b1222]/90 border border-slate-800 p-5 shadow-xl">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-bold font-mono text-slate-100">
              Normalized Policy Entropy
            </h3>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">Score:</span>
            <span className="text-purple-400 font-bold px-2 py-0.5 rounded bg-purple-950/50 border border-purple-800">
              {currentEntropy.toFixed(3)}
            </span>
          </div>
        </div>

        {entropies.length === 0 ? (
          <div className="h-[160px] flex items-center justify-center text-xs font-mono text-slate-500">
            Awaiting AI actions to compute policy entropy...
          </div>
        ) : (
          <div className="w-full overflow-hidden">
            <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full h-[160px]">
              {/* Threshold line at 0.2 (Low exploration) */}
              <line
                x1={padding.left}
                y1={getEntropyY(0.2)}
                x2={chartWidth - padding.right}
                y2={getEntropyY(0.2)}
                stroke="#6366f1"
                strokeDasharray="4 4"
                strokeWidth="1"
              />
              <text
                x={chartWidth - padding.right}
                y={getEntropyY(0.2) - 4}
                fill="#6366f1"
                fontSize="9"
                textAnchor="end"
                fontFamily="monospace"
              >
                0.20 (Low Exploration Boundary)
              </text>

              {/* Entropy Curve */}
              {entropies.length > 1 && (
                <polyline
                  fill="none"
                  stroke="#a855f7"
                  strokeWidth="2.5"
                  points={entropyPoints}
                />
              )}

              {/* Points */}
              {entropies.map((val, idx) => (
                <circle
                  key={idx}
                  cx={getRewardX(idx, entropies.length)}
                  cy={getEntropyY(val)}
                  r="3.5"
                  fill="#c084fc"
                  stroke="#0b1222"
                  strokeWidth="1.5"
                />
              ))}

              {/* Labels */}
              <text x={padding.left - 6} y={padding.top + 5} fill="#64748b" fontSize="9" textAnchor="end" fontFamily="monospace">
                1.00
              </text>
              <text x={padding.left - 6} y={chartHeight - padding.bottom} fill="#64748b" fontSize="9" textAnchor="end" fontFamily="monospace">
                0.00
              </text>
            </svg>
          </div>
        )}

        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mt-1">
          <span>0.0 = Deterministic Exploitation</span>
          <span>1.0 = Maximum Stochastic Exploration</span>
        </div>
      </div>
    </div>
  );
}
