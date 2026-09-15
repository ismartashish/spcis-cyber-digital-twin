import React, { useMemo } from 'react';
import { Shield, ShieldAlert, Globe, Server, Database, Key, Lock, AlertTriangle, Bug, Award } from 'lucide-react';

export default function TopologyGraph({ topology, onSelectNode, selectedNodeId, lastAction }) {
  const nodes = topology?.nodes || [];
  const edges = topology?.edges || [];

  // Compute node layout positions
  const nodePositions = useMemo(() => {
    const pos = {};
    const width = 800;
    const height = 460;
    
    // Fallback predefined positions for standard 3-tier architecture or dynamic layout
    const predefined = {
      'web': { x: 120, y: height / 2 },
      'api': { x: 360, y: height / 2 - 40 },
      'auth': { x: 580, y: 120 },
      'db': { x: 680, y: 340 },
    };

    // Calculate layered positions for arbitrary topologies
    const inDegree = {};
    nodes.forEach(n => {
      inDegree[n.id] = (n.reachable_from || []).length;
    });

    const tier0 = nodes.filter(n => (n.reachable_from || []).length === 0);
    const tierN = nodes.filter(n => n.is_crown_jewel);
    const tierMid = nodes.filter(n => (n.reachable_from || []).length > 0 && !n.is_crown_jewel);

    nodes.forEach((n, idx) => {
      if (predefined[n.id]) {
        pos[n.id] = predefined[n.id];
      } else {
        // Dynamic layered layout
        const total = nodes.length;
        const xStep = (width - 240) / Math.max(1, (tier0.length > 0 ? 3 : 2));
        let x = 120;
        let y = 100 + (idx * 90) % (height - 180);

        if ((n.reachable_from || []).length === 0) {
          x = 120;
          y = 100 + idx * 120;
        } else if (n.is_crown_jewel) {
          x = width - 120;
          y = height / 2;
        } else {
          x = 120 + xStep;
          y = 120 + idx * 80;
        }
        pos[n.id] = { x, y };
      }
    });

    return pos;
  }, [nodes]);

  const getNodeIcon = (node) => {
    if (node.is_crown_jewel) return <Award className="w-5 h-5 text-amber-400" />;
    switch (node.role) {
      case 'web': return <Globe className="w-5 h-5 text-cyan-400" />;
      case 'api': return <Server className="w-5 h-5 text-blue-400" />;
      case 'auth': return <Key className="w-5 h-5 text-purple-400" />;
      case 'db': return <Database className="w-5 h-5 text-emerald-400" />;
      default: return <Server className="w-5 h-5 text-slate-400" />;
    }
  };

  const getStatusBorder = (node) => {
    if (node.isolated) return 'stroke-amber-500 stroke-dasharray-4 shadow-[0_0_15px_rgba(245,158,11,0.5)]';
    if (node.compromised) return 'stroke-red-500 shadow-[0_0_20px_rgba(239,68,68,0.7)]';
    if (node.known) return 'stroke-cyan-400';
    return 'stroke-slate-600';
  };

  return (
    <div className="relative w-full h-[520px] rounded-2xl bg-[#090e1c] border border-slate-800/80 overflow-hidden flex flex-col justify-between cyber-grid shadow-2xl">
      {/* Top Overlay Info */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-3">
        <div className="px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs font-mono text-slate-300 backdrop-blur-md flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
          <span>TOPOLOGY: <strong>{topology?.name || '3-tier-cluster'}</strong></span>
        </div>

        {/* Legend */}
        <div className="hidden lg:flex items-center gap-3 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-[11px] font-mono text-slate-400 backdrop-blur-md">
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> Compromised</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Isolated</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span> Discovered</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-slate-600"></span> Clean/Unknown</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-400 ring-2 ring-amber-400/40"></span> Crown Jewel</span>
        </div>
      </div>

      {/* Interactive SVG Canvas */}
      <svg className="w-full h-full" viewBox="0 0 800 460">
        <defs>
          <linearGradient id="edgeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0.6" />
          </linearGradient>
          <linearGradient id="edgeCompromised" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ef4444" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.9" />
          </linearGradient>
          <marker id="arrow" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#64748b" />
          </marker>
          <marker id="arrowActive" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#ef4444" />
          </marker>
          {/* Node Glow Filters */}
          <filter id="glowRed" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="glowGold" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="8" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Ambient Grid Lines & Radar Pulse */}
        <circle cx="400" cy="230" r="180" fill="none" stroke="#1e293b" strokeWidth="1" strokeDasharray="4 8" opacity="0.5" />
        <circle cx="400" cy="230" r="300" fill="none" stroke="#1e293b" strokeWidth="1" strokeDasharray="6 12" opacity="0.3" />

        {/* Edges */}
        {edges.map((edge, idx) => {
          const src = nodePositions[edge.source];
          const tgt = nodePositions[edge.target];
          if (!src || !tgt) return null;

          const srcNode = nodes.find(n => n.id === edge.source);
          const tgtNode = nodes.find(n => n.id === edge.target);

          const isEdgeCompromised = srcNode?.compromised && tgtNode?.compromised;
          const isEdgeActive = srcNode?.compromised;
          const isCut = tgtNode?.isolated;

          // Curved path calculation
          const dx = tgt.x - src.x;
          const dy = tgt.y - src.y;
          const cx1 = src.x + dx * 0.5;
          const cy1 = src.y;
          const cx2 = src.x + dx * 0.5;
          const cy2 = tgt.y;
          const pathD = `M ${src.x} ${src.y} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${tgt.x} ${tgt.y}`;

          return (
            <g key={`edge-${edge.source}-${edge.target}-${idx}`}>
              <path
                d={pathD}
                fill="none"
                stroke={isCut ? '#475569' : isEdgeCompromised ? '#ef4444' : isEdgeActive ? '#38bdf8' : '#334155'}
                strokeWidth={isEdgeCompromised ? 2.5 : 1.5}
                strokeDasharray={isCut ? '4 4' : isEdgeCompromised ? 'none' : '6 4'}
                opacity={isCut ? 0.3 : isEdgeCompromised ? 0.9 : 0.6}
                markerEnd={isEdgeCompromised ? 'url(#arrowActive)' : 'url(#arrow)'}
              />
              {/* Traveling Packet Animation along active edge */}
              {isEdgeActive && !isCut && (
                <circle r="3" fill={isEdgeCompromised ? '#ff2a5f' : '#38bdf8'}>
                  <animateMotion
                    path={pathD}
                    dur={isEdgeCompromised ? '2s' : '3.5s'}
                    repeatCount="indefinite"
                  />
                </circle>
              )}
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => {
          const pos = nodePositions[node.id];
          if (!pos) return null;

          const isSelected = selectedNodeId === node.id;
          const unpatchedCount = (node.vulnerabilities || []).filter(v => !v.patched).length;

          return (
            <g
              key={`node-${node.id}`}
              transform={`translate(${pos.x}, ${pos.y})`}
              className="cursor-pointer transition-transform duration-200 hover:scale-110"
              onClick={() => onSelectNode(node)}
            >
              {/* Pulsing Aura if Compromised or Crown Jewel */}
              {node.compromised && (
                <circle
                  r="38"
                  fill="none"
                  stroke="#ef4444"
                  strokeWidth="1.5"
                  opacity="0.4"
                  className="animate-ping"
                />
              )}
              {node.is_crown_jewel && !node.compromised && (
                <circle
                  r="38"
                  fill="none"
                  stroke="#f59e0b"
                  strokeWidth="1.5"
                  opacity="0.3"
                  className="animate-pulse"
                />
              )}

              {/* Outer Selection Highlight Ring */}
              {isSelected && (
                <circle
                  r="36"
                  fill="none"
                  stroke="#00f0ff"
                  strokeWidth="2.5"
                  strokeDasharray="6 4"
                />
              )}

              {/* Main Node Background Circle */}
              <circle
                r="28"
                fill={node.compromised ? '#1e1017' : node.isolated ? '#1f1a10' : '#0f172a'}
                stroke={node.isolated ? '#f59e0b' : node.compromised ? '#ef4444' : node.known ? '#38bdf8' : '#475569'}
                strokeWidth={node.compromised || node.isolated ? '2.5' : '1.8'}
                filter={node.compromised ? 'url(#glowRed)' : node.is_crown_jewel ? 'url(#glowGold)' : undefined}
              />

              {/* Center Node Icon (SVG FO) */}
              <foreignObject x="-12" y="-12" width="24" height="24" className="pointer-events-none">
                <div className="w-full h-full flex items-center justify-center">
                  {getNodeIcon(node)}
                </div>
              </foreignObject>

              {/* Vulnerability Alert Badge (Top Right) */}
              {unpatchedCount > 0 && !node.isolated && (
                <g transform="translate(18, -18)">
                  <circle r="9" fill={node.compromised ? '#ef4444' : '#f97316'} />
                  <text
                    textAnchor="middle"
                    dy="3.5"
                    fill="#ffffff"
                    fontSize="9"
                    fontWeight="bold"
                    fontFamily="monospace"
                  >
                    {unpatchedCount}
                  </text>
                </g>
              )}

              {/* Isolated Lock Icon (Top Right if isolated) */}
              {node.isolated && (
                <g transform="translate(18, -18)">
                  <circle r="9" fill="#f59e0b" />
                  <foreignObject x="-6" y="-6" width="12" height="12">
                    <Lock className="w-3 h-3 text-slate-950 font-bold" />
                  </foreignObject>
                </g>
              )}

              {/* Node Label Below */}
              <text
                textAnchor="middle"
                y="45"
                fill="#f8fafc"
                fontSize="12"
                fontWeight="600"
                fontFamily="monospace"
                className="select-none drop-shadow"
              >
                {node.id}
              </text>

              {/* Sub-label / Role */}
              <text
                textAnchor="middle"
                y="58"
                fill={node.compromised ? '#f87171' : node.isolated ? '#fbbf24' : '#94a3b8'}
                fontSize="10"
                fontFamily="sans-serif"
                className="select-none tracking-wide uppercase font-medium"
              >
                {node.status}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Bottom Hint */}
      <div className="px-5 py-2.5 bg-slate-950/70 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400 font-mono">
        <span className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
          <span>Click any node to inspect CVEs, network routing, and exploit vulnerability scores</span>
        </span>
        <span className="hidden sm:inline text-slate-500">
          Last event: <span className="text-slate-300">{lastAction || 'None'}</span>
        </span>
      </div>
    </div>
  );
}
