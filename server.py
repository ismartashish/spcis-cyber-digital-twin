"""
server.py
=========
FastAPI Backend Server for SPCIS (Self-Playing Cyber Immune System).
Bridges the Python digital twin, Red PPO / heuristic agents, Blue defender,
formal verification invariants, and Arena self-play league with the web frontend.
"""
from __future__ import annotations

import copy
import json
import math
import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import uvicorn
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from digital_twin.env import Topology, TwinEnv
from red_agent.policy import HeuristicRedPolicy, dispatch as red_dispatch
from blue_agent.policy import HeuristicBluePolicy, dispatch as blue_dispatch
from red_agent.train import FlatRedGymEnv
from verification import invariants
from orchestrator.arena import run_episode, RewardBreakdown
from explainability.report import render_episode

# Optional PPO model loading
try:
    from sb3_contrib import MaskablePPO
except ImportError:
    MaskablePPO = None

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "configs", "twin_topology.yaml")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "runs", "red_ppo.zip")
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")

app = FastAPI(
    title="SPCIS API",
    description="REST API for Self-Playing Cyber Immune System Digital Twin",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Global State Manager
# -----------------------------------------------------------------------------

class SimulationSession:
    def __init__(self):
        self.topology_config = None
        self.model = None
        self.model_loaded = False
        self.env: Optional[FlatRedGymEnv] = None
        self.raw_env: Optional[TwinEnv] = None
        self.observation = None
        self.policy_mode: str = "ppo"  # "ppo" or "heuristic"
        self.seed: int = 42

        self.step_count: int = 0
        self.episode_reward: float = 0.0
        self.done: bool = False
        self.crown_jewel_compromised: bool = False

        self.events: List[Dict[str, Any]] = []
        self.reward_history: List[float] = []
        self.entropy_history: List[float] = []
        self.action_history: List[str] = []

        self.red_stats = {
            "scans": {"attempts": 0, "successes": 0},
            "exploits": {"attempts": 0, "successes": 0},
            "pivots": {"attempts": 0, "successes": 0},
        }
        self.blue_stats = {
            "detections": 0,
            "isolations": 0,
            "patches": 0,
            "violations": 0,
        }
        self.last_action: str = "None"
        self.last_reward: float = 0.0
        self.last_invariant_checks: List[Dict[str, Any]] = []

        self.load_model()

    def load_topology(self) -> Topology:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return Topology.from_dict(data)

    def load_model(self):
        if MaskablePPO is not None and os.path.exists(MODEL_PATH):
            try:
                self.model = MaskablePPO.load(MODEL_PATH, device="cpu")
                self.model_loaded = True
            except Exception as e:
                print(f"[WARN] Failed to load PPO model: {e}")
                self.model = None
                self.model_loaded = False
        else:
            self.model = None
            self.model_loaded = False

    def reset(self, seed: Optional[int] = None, policy_mode: Optional[str] = None):
        if seed is not None:
            self.seed = seed
        else:
            self.seed = int(np.random.randint(0, 1_000_000))

        if policy_mode:
            self.policy_mode = policy_mode

        topology = self.load_topology()
        self.env = FlatRedGymEnv(topology, max_vulns_per_node=4, max_steps=40)
        self.observation, _ = self.env.reset(seed=self.seed)

        self.step_count = 0
        self.episode_reward = 0.0
        self.done = False
        self.crown_jewel_compromised = False

        self.events = []
        self.reward_history = []
        self.entropy_history = []
        self.action_history = []

        self.red_stats = {
            "scans": {"attempts": 0, "successes": 0},
            "exploits": {"attempts": 0, "successes": 0},
            "pivots": {"attempts": 0, "successes": 0},
        }
        self.blue_stats = {
            "detections": 0,
            "isolations": 0,
            "patches": 0,
            "violations": 0,
        }
        self.last_action = "Simulation initialized"
        self.last_reward = 0.0

        # Initial invariant checks
        init_checks = invariants.check_state(self.env.env)
        self.last_invariant_checks = [asdict(c) for c in init_checks]

        return self.get_full_state()

    def calculate_entropy(self, obs) -> float:
        if self.model is None or not self.model_loaded:
            return 0.0
        try:
            obs_array = np.asarray(obs, dtype=np.float32)
            obs_tensor, _ = self.model.policy.obs_to_tensor(obs_array)
            with torch.no_grad():
                dist = self.model.policy.get_distribution(obs_tensor)
                actual_entropy = float(dist.distribution.entropy().mean().cpu().item())
            n_actions = int(self.model.action_space.n)
            max_entropy = math.log(max(2, n_actions))
            norm = actual_entropy / max_entropy if max_entropy > 0 else 0.0
            return float(np.clip(norm, 0.0, 1.0))
        except Exception:
            return 0.0

    def describe_action(self, action_idx: int) -> str:
        if self.env is None:
            return "UNKNOWN"
        action = self.env.actions[action_idx]
        action_name = type(action).__name__
        if action_name == "ExploitAction":
            return f"EXPLOIT -> {action.node_id} (slot {action.vuln_slot})"
        if action_name == "ScanAction":
            return f"SCAN -> {action.node_id}"
        if action_name == "PivotAction":
            return f"PIVOT -> {action.source_id} -> {action.target_id}"
        return "UNKNOWN"

    def step(self) -> Dict[str, Any]:
        if self.env is None:
            self.reset()
        if self.done:
            return self.get_full_state()

        # Decide Red action
        action_idx = 0
        use_ppo = (self.policy_mode == "ppo" and self.model is not None and self.model_loaded)
        if use_ppo:
            action_masks = self.env.action_masks()
            act, _ = self.model.predict(self.observation, action_masks=action_masks, deterministic=True)
            action_idx = int(act)
        else:
            mask = self.env.action_masks()
            valid_actions = np.flatnonzero(mask)
            if len(valid_actions) > 0:
                action_idx = int(np.random.choice(valid_actions))
            else:
                action_idx = 0

        action_desc = self.describe_action(action_idx)

        # Step Gym env
        new_obs, reward, term, trunc, info = self.env.step(action_idx)
        self.observation = new_obs
        self.step_count += 1
        self.episode_reward += float(reward)
        self.last_reward = float(reward)
        self.last_action = action_desc
        self.done = bool(term or trunc)

        # Entropy
        entropy_val = self.calculate_entropy(new_obs)
        self.entropy_history.append(entropy_val)
        self.reward_history.append(float(reward))
        self.action_history.append(action_desc)

        # Action accounting
        action_type = info.get("action_type", "unknown")
        raw_result = info.get("raw_result", {})
        ok = bool(raw_result.get("ok", False))
        detected = bool(raw_result.get("detected", False))

        if action_type in ("exploit", "crown_jewel_exploit"):
            self.red_stats["exploits"]["attempts"] += 1
            if ok:
                self.red_stats["exploits"]["successes"] += 1
        elif action_type == "pivot":
            self.red_stats["pivots"]["attempts"] += 1
            if ok:
                self.red_stats["pivots"]["successes"] += 1
        elif action_type == "scan":
            self.red_stats["scans"]["attempts"] += 1
            if ok:
                self.red_stats["scans"]["successes"] += 1

        if detected:
            self.blue_stats["detections"] += 1

        if info.get("crown_jewel_compromised", False):
            self.crown_jewel_compromised = True

        # Invariant checks for verification monitor
        check_results = invariants.check_state(self.env.env)
        self.last_invariant_checks = [asdict(c) for c in check_results]
        if not invariants.all_passed(check_results):
            self.blue_stats["violations"] += 1

        # Check latest blue events from env log if any
        for ev in reversed(self.env.env.event_log):
            if ev.get("actor") == "blue":
                b_action = ev.get("action", ("noop",))
                if b_action[0] == "isolate":
                    self.blue_stats["isolations"] += 1
                elif b_action[0] == "patch":
                    self.blue_stats["patches"] += 1
                break

        # Record event
        event = {
            "step": self.step_count,
            "action": action_desc,
            "action_type": action_type,
            "reward": float(reward),
            "result": "SUCCESS" if ok else "FAILED",
            "detected": detected,
            "details": raw_result.get("reason", "") or raw_result.get("message", ""),
            "crown_jewel": self.crown_jewel_compromised,
        }
        self.events.insert(0, event)
        if len(self.events) > 60:
            self.events = self.events[:60]

        return self.get_full_state()

    def get_full_state(self) -> Dict[str, Any]:
        if self.env is None:
            self.reset()

        topo_env = self.env.env
        nodes_data = []
        edges_data = []

        for node_id in self.env.node_ids:
            node = topo_env.topology.nodes[node_id]
            is_compromised = bool(node.compromised)
            is_isolated = node_id in topo_env.isolated_nodes
            is_known = node_id in topo_env.red_known_nodes

            if is_isolated:
                status = "ISOLATED"
            elif is_compromised:
                status = "COMPROMISED"
            elif is_known:
                status = "DISCOVERED"
            else:
                status = "UNKNOWN"

            vulns = []
            for v in node.vulnerabilities:
                vulns.append({
                    "vuln_id": v.vuln_id,
                    "vuln_class": v.vuln_class,
                    "severity": v.severity,
                    "exploitability": v.exploitability,
                    "patched": v.patched,
                })

            nodes_data.append({
                "id": node_id,
                "role": node.role,
                "status": status,
                "is_crown_jewel": node.is_crown_jewel,
                "compromised": is_compromised,
                "isolated": is_isolated,
                "known": is_known,
                "detection_sensitivity": node.detection_sensitivity,
                "vulnerabilities": vulns,
                "reachable_from": node.reachable_from,
            })

            for src in node.reachable_from:
                if src in self.env.node_ids:
                    edges_data.append({
                        "source": src,
                        "target": node_id,
                    })

        exploit_attempts = max(1, self.red_stats["exploits"]["attempts"])
        pivot_attempts = max(1, self.red_stats["pivots"]["attempts"])
        scan_attempts = max(1, self.red_stats["scans"]["attempts"])

        kpis = {
            "step": self.step_count,
            "episode_reward": round(self.episode_reward, 3),
            "entropy": round(self.entropy_history[-1] if self.entropy_history else 0.0, 3),
            "crown_jewel_compromised": self.crown_jewel_compromised,
            "done": self.done,
            "exploit_rate": round(self.red_stats["exploits"]["successes"] / exploit_attempts * 100, 1),
            "pivot_rate": round(self.red_stats["pivots"]["successes"] / pivot_attempts * 100, 1),
            "scan_rate": round(self.red_stats["scans"]["successes"] / scan_attempts * 100, 1),
            "total_exploits": self.red_stats["exploits"]["attempts"],
            "total_pivots": self.red_stats["pivots"]["attempts"],
            "total_scans": self.red_stats["scans"]["attempts"],
            "blue_detections": self.blue_stats["detections"],
            "blue_isolations": self.blue_stats["isolations"],
            "blue_patches": self.blue_stats["patches"],
            "blue_violations": self.blue_stats["violations"],
        }

        return {
            "session": {
                "seed": self.seed,
                "policy_mode": self.policy_mode,
                "model_loaded": self.model_loaded,
                "last_action": self.last_action,
                "last_reward": self.last_reward,
            },
            "kpis": kpis,
            "topology": {
                "name": topo_env.topology.name,
                "nodes": nodes_data,
                "edges": edges_data,
            },
            "events": self.events,
            "reward_history": self.reward_history,
            "entropy_history": self.entropy_history,
            "invariant_checks": self.last_invariant_checks,
        }


session = SimulationSession()


# -----------------------------------------------------------------------------
# REST API Models
# -----------------------------------------------------------------------------

class ResetRequest(BaseModel):
    seed: Optional[int] = None
    policy_mode: Optional[str] = "ppo"


class AutoStepRequest(BaseModel):
    steps: int = 5


class BenchmarkRequest(BaseModel):
    episodes: int = 5
    red_policy: str = "heuristic"  # "heuristic" or "ppo"
    max_steps: int = 40


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------

@app.get("/api/status")
def get_status():
    return {
        "status": "online",
        "service": "SPCIS Cyber Defense Engine",
        "model_loaded": session.model_loaded,
        "model_file": MODEL_PATH,
        "model_exists": os.path.exists(MODEL_PATH),
        "policy_mode": session.policy_mode,
        "step": session.step_count,
        "done": session.done,
    }


@app.get("/api/topology")
def get_topology():
    return session.get_full_state()["topology"]


@app.get("/api/simulation/state")
def get_state():
    return session.get_full_state()


@app.post("/api/simulation/reset")
def reset_simulation(req: ResetRequest = ResetRequest()):
    return session.reset(seed=req.seed, policy_mode=req.policy_mode)


@app.post("/api/simulation/step")
def step_simulation():
    return session.step()


@app.post("/api/simulation/auto")
def auto_step_simulation(req: AutoStepRequest):
    steps_to_run = min(40, max(1, req.steps))
    for _ in range(steps_to_run):
        if session.done:
            break
        session.step()
    return session.get_full_state()


@app.post("/api/arena/benchmark")
def run_benchmark(req: BenchmarkRequest):
    topo = session.load_topology()
    blue_pol = HeuristicBluePolicy()
    red_pol = HeuristicRedPolicy()

    episodes_data = []
    crown_compromises = 0
    total_red_reward = 0.0
    total_blue_reward = 0.0
    total_steps = 0

    for i in range(req.episodes):
        ep_seed = 1000 + i
        summary = run_episode(
            topology=topo,
            red_policy=red_pol,
            blue_policy=blue_pol,
            max_steps=req.max_steps,
            seed=ep_seed,
        )
        episodes_data.append(summary)
        if summary.get("crown_jewel_compromised"):
            crown_compromises += 1
        total_red_reward += summary.get("red_reward", 0.0)
        total_blue_reward += summary.get("blue_reward", 0.0)
        total_steps += summary.get("steps_taken", 0)

    n = max(1, req.episodes)
    benchmark_summary = {
        "n_episodes": req.episodes,
        "crown_jewel_compromise_rate": crown_compromises / n,
        "crown_jewel_compromised_count": crown_compromises,
        "blue_containment_rate": (n - crown_compromises) / n,
        "avg_red_reward": round(total_red_reward / n, 2),
        "avg_blue_reward": round(total_blue_reward / n, 2),
        "avg_steps": round(total_steps / n, 1),
        "episodes": episodes_data,
    }

    # Generate markdown report
    report_md = f"# SPCIS Arena Benchmark Report\n\n"
    report_md += f"**Episodes:** {req.episodes} | **Red Policy:** {red_pol.__class__.__name__} | **Blue Policy:** {blue_pol.__class__.__name__}\n\n"
    report_md += f"- **Crown Jewel Compromise Rate:** {benchmark_summary['crown_jewel_compromise_rate']:.1%}\n"
    report_md += f"- **Blue Containment Rate:** {benchmark_summary['blue_containment_rate']:.1%}\n"
    report_md += f"- **Average Red Reward:** {benchmark_summary['avg_red_reward']}\n"
    report_md += f"- **Average Blue Reward:** {benchmark_summary['avg_blue_reward']}\n"
    report_md += f"- **Average Steps to Termination:** {benchmark_summary['avg_steps']}\n\n"
    report_md += "## Detailed Episodes\n\n"
    for ep in episodes_data:
        report_md += render_episode(ep) + "\n---\n"

    benchmark_summary["report_markdown"] = report_md
    return benchmark_summary


@app.get("/api/report/latest")
def get_latest_report():
    if not session.events:
        return {"report": "No simulation activity recorded yet. Run an episode to generate an incident report."}

    ep_dict = {
        "seed": session.seed,
        "red_policy": session.policy_mode.upper(),
        "blue_policy": "HeuristicBluePolicy",
        "crown_jewel_compromised": session.crown_jewel_compromised,
        "steps_taken": session.step_count,
        "red_reward": session.episode_reward,
        "blue_reward": float(session.blue_stats["patches"] * 2 + session.blue_stats["isolations"] - session.blue_stats["violations"] * 5),
        "event_log": [
            {
                "step": e["step"],
                "actor": "red",
                "action": e["action"],
                "result": {
                    "ok": e["result"] == "SUCCESS",
                    "detected": e.get("detected", False),
                    "reason": e.get("details", ""),
                }
            }
            for e in reversed(session.events)
        ],
        "blue_reward_events": [
            {
                "action": ("patch/isolate", "auto-defense"),
                "reward": 1.0,
                "invariant_checks": session.last_invariant_checks,
            }
        ] if session.blue_stats["patches"] or session.blue_stats["isolations"] else []
    }

    report_md = render_episode(ep_dict)
    return {
        "report": report_md,
        "episode_data": ep_dict,
    }


# -----------------------------------------------------------------------------
# Static Frontend Serving
# -----------------------------------------------------------------------------

if os.path.exists(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.exists(file_path) and not os.path.isdir(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    def index():
        return HTMLResponse(
            """
            <!DOCTYPE html>
            <html>
            <head><title>SPCIS API</title></head>
            <body style="font-family: sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px;">
                <h1>🛡️ SPCIS API Server Online</h1>
                <p>FastAPI backend is active. Build the frontend in <code>frontend/</code> to enable the UI.</p>
                <p><a href="/docs" style="color: #38bdf8;">View Swagger API Documentation</a></p>
            </body>
            </html>
            """
        )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SPCIS Web Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port")
    parser.add_argument("--reload", action="store_true", help="Auto reload")
    args = parser.parse_args()

    print(f"🚀 Starting SPCIS Cyber Immune System Server on http://{args.host}:{args.port}")
    uvicorn.run("server:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
