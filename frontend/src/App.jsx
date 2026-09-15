import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import TopologyGraph from './components/TopologyGraph';
import NodeDrawer from './components/NodeDrawer';
import ControlPanel from './components/ControlPanel';
import AgentTelemetry from './components/AgentTelemetry';
import InvariantsCard from './components/InvariantsCard';
import AnalyticsCharts from './components/AnalyticsCharts';
import EventTimeline from './components/EventTimeline';
import ArenaBenchmark from './components/ArenaBenchmark';
import ReportModal from './components/ReportModal';
import { api } from './api';
import { Network, Activity, BarChart2, BookOpen, AlertCircle, RefreshCw } from 'lucide-react';

export default function App() {
  const [state, setState] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [isStepping, setIsStepping] = useState(false);
  const [policyMode, setPolicyMode] = useState('ppo');
  const [seed, setSeed] = useState(42);
  const [isConnected, setIsConnected] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard', 'analytics', 'timeline', 'docs'

  // Modals
  const [showBenchmark, setShowBenchmark] = useState(false);
  const [showReport, setShowReport] = useState(false);

  useEffect(() => {
    fetchState();
  }, []);

  const fetchState = async () => {
    try {
      const data = await api.getState();
      setState(data);
      setIsConnected(true);
      if (data.session) {
        setPolicyMode(data.session.policy_mode || 'ppo');
        setSeed(data.session.seed || 42);
      }
    } catch (err) {
      console.warn('Backend connection issue:', err);
      setIsConnected(false);
    }
  };

  const handleStep = async () => {
    setIsStepping(true);
    try {
      const data = await api.stepSimulation();
      setState(data);
      // Keep selected node in sync if drawer is open
      if (selectedNode) {
        const updated = data.topology?.nodes?.find(n => n.id === selectedNode.id);
        if (updated) setSelectedNode(updated);
      }
    } catch (err) {
      console.error('Step error:', err);
    } finally {
      setIsStepping(false);
    }
  };

  const handleAutoStep = async (steps = 5) => {
    setIsStepping(true);
    try {
      const data = await api.autoStepSimulation(steps);
      setState(data);
      if (selectedNode) {
        const updated = data.topology?.nodes?.find(n => n.id === selectedNode.id);
        if (updated) setSelectedNode(updated);
      }
    } catch (err) {
      console.error('Auto step error:', err);
    } finally {
      setIsStepping(false);
    }
  };

  const handleReset = async (newSeed = null, newPolicy = null) => {
    setIsStepping(true);
    try {
      const data = await api.resetSimulation(newSeed !== null ? newSeed : seed, newPolicy || policyMode);
      setState(data);
      setSelectedNode(null);
    } catch (err) {
      console.error('Reset error:', err);
    } finally {
      setIsStepping(false);
    }
  };

  const modelLoaded = Boolean(state?.session?.model_loaded);
  const isDone = Boolean(state?.kpis?.done);

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Header */}
      <Header
        state={state}
        onReset={() => handleReset(seed, policyMode)}
        onOpenBenchmark={() => setShowBenchmark(true)}
        onOpenReport={() => setShowReport(true)}
        isConnected={isConnected}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-[1700px] w-full mx-auto px-4 sm:px-6 py-5 space-y-6">
        {/* Navigation Tabs */}
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all ${
                activeTab === 'dashboard'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Network className="w-4 h-4" />
              <span>DIGITAL TWIN & COCKPIT</span>
            </button>

            <button
              onClick={() => setActiveTab('analytics')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all ${
                activeTab === 'analytics'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <BarChart2 className="w-4 h-4" />
              <span>RL ANALYTICS</span>
            </button>

            <button
              onClick={() => setActiveTab('timeline')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all ${
                activeTab === 'timeline'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>TIMELINE & MITRE LOGS</span>
            </button>

            <button
              onClick={() => setActiveTab('docs')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all ${
                activeTab === 'docs'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>SYSTEM ARCHITECTURE</span>
            </button>
          </div>

          <div className="hidden md:flex items-center gap-2 text-xs font-mono text-slate-400">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
            <span>SIMULATION CLOCK: TICK {state?.kpis?.step || 0}</span>
          </div>
        </div>

        {/* Tab 1: Dashboard */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Simulation Controls */}
            <ControlPanel
              onStep={handleStep}
              onAutoStep={handleAutoStep}
              onReset={(s, p) => handleReset(s, p)}
              isStepping={isStepping}
              policyMode={policyMode}
              setPolicyMode={setPolicyMode}
              modelLoaded={modelLoaded}
              isDone={isDone}
              seed={seed}
              setSeed={setSeed}
            />

            {/* Topology Graph Visualizer */}
            <TopologyGraph
              topology={state?.topology}
              onSelectNode={(node) => setSelectedNode(node)}
              selectedNodeId={selectedNode?.id}
              lastAction={state?.session?.last_action}
            />

            {/* Red vs Blue Live Telemetry */}
            <AgentTelemetry state={state} />

            {/* Formal Invariants Gate */}
            <InvariantsCard invariantChecks={state?.invariant_checks} />

            {/* Quick Timeline Stream */}
            <EventTimeline events={state?.events} />
          </div>
        )}

        {/* Tab 2: RL Analytics */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <AnalyticsCharts
              rewardHistory={state?.reward_history}
              entropyHistory={state?.entropy_history}
            />
            <AgentTelemetry state={state} />
            <InvariantsCard invariantChecks={state?.invariant_checks} />
          </div>
        )}

        {/* Tab 3: Timeline */}
        {activeTab === 'timeline' && (
          <div className="space-y-6">
            <EventTimeline events={state?.events} />
            <InvariantsCard invariantChecks={state?.invariant_checks} />
          </div>
        )}

        {/* Tab 4: Architecture Docs */}
        {activeTab === 'docs' && (
          <div className="rounded-2xl bg-[#0b1222]/90 border border-slate-800 p-8 shadow-xl space-y-6 max-w-4xl mx-auto">
            <div className="border-b border-slate-800 pb-4">
              <h2 className="text-xl font-bold font-mono text-cyan-400">
                Self-Playing Cyber Immune System (SPCIS) Architecture
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Continuous autonomous red-team vs. blue-team self-play inside an isolated digital twin with formal invariant safety
              </p>
            </div>

            <div className="space-y-4 text-xs font-mono text-slate-300 leading-relaxed">
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                <h3 className="text-sm font-bold text-slate-100 mb-1 flex items-center gap-2">
                  <span className="text-red-400">1. Red Agent (Adversarial RL)</span>
                </h3>
                <p className="text-slate-400">
                  Explores network topology through actions: SCAN (discover open attack surface), EXPLOIT (target specific CVE with exploitability probability), and PIVOT (lateral movement from compromised nodes). Learns optimal attack paths using Maskable PPO.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                <h3 className="text-sm font-bold text-slate-100 mb-1 flex items-center gap-2">
                  <span className="text-cyan-400">2. Blue Defender (Adaptive Immune Response)</span>
                </h3>
                <p className="text-slate-400">
                  Observes telemetry anomalies to detect attacks. Proposes automated defensive countermeasures: node quarantine/isolation and targeted CVE vulnerability patching.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                <h3 className="text-sm font-bold text-slate-100 mb-1 flex items-center gap-2">
                  <span className="text-emerald-400">3. Formal Invariant Verification Gate</span>
                </h3>
                <p className="text-slate-400">
                  Every blue defense action is checked against formal predicates (e.g. <code>no_full_isolation</code> and <code>web_tier_reachable</code>). Any patch or isolation breaking system SLAs is rejected and rolled back with a -R penalty, preventing degenerate self-dos solutions.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                <h3 className="text-sm font-bold text-slate-100 mb-1 flex items-center gap-2">
                  <span className="text-amber-400">4. Explainability & Reproducible Proof-of-Concept</span>
                </h3>
                <p className="text-slate-400">
                  Every positive reward is strictly tied to a reproducible causal chain recorded in the deterministic event log, exportable as an executive incident report.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Node Inspector Drawer */}
      <NodeDrawer
        node={selectedNode}
        onClose={() => setSelectedNode(null)}
      />

      {/* Arena Benchmark Modal */}
      {showBenchmark && (
        <ArenaBenchmark
          onClose={() => setShowBenchmark(false)}
          modelLoaded={modelLoaded}
        />
      )}

      {/* Report Modal */}
      {showReport && (
        <ReportModal
          onClose={() => setShowReport(false)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#070b14] py-4 px-6 text-center text-xs font-mono text-slate-500">
        SPCIS Cyber Immune System • Autonomous Red vs Blue Co-Evolution • Maskable PPO & Formal Methods
      </footer>
    </div>
  );
}
