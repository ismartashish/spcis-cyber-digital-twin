"""
blue_agent.policy
==================

Baseline BLUE policy against digital_twin.env.TwinEnv.

Split into two conceptual sub-policies, per docs/ARCHITECTURE.md §4,
even though this heuristic baseline implements them as one class:

  - detection: inspect the event log for red actions flagged
    `detected=True` by the environment (a stand-in for a real
    anomaly/IDS signal in a production twin).
  - response: for a detected compromise, patch the exploited
    vulnerability; every patch this heuristic proposes is checked
    against verification.invariants before being counted as "applied"
    — see orchestrator/arena.py for where that gate is enforced.

This baseline never isolates a node pre-emptively (that's a bigger
hammer with a bigger `-R_break` risk) — it only isolates a node after
repeated detections against it, which is closer to a realistic
graduated response.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from digital_twin.env import TwinEnv


class HeuristicBluePolicy:
    name = "heuristic_blue_v0"

    def __init__(self, isolate_after_detections: int = 2):
        self.detections_per_node: dict[str, int] = defaultdict(int)
        self.isolate_after_detections = isolate_after_detections

    def act(self, env: TwinEnv) -> tuple:
        # look at the most recent red event this tick
        recent_red = [e for e in env.event_log if e["actor"] == "red" and e["step"] == env.step_count]
        for event in recent_red:
            result = event["result"]
            action = event["action"]
            if action[0] == "exploit" and result.get("detected"):
                node_id = action[1]
                vuln_id = action[2]
                self.detections_per_node[node_id] += 1
                if self.detections_per_node[node_id] >= self.isolate_after_detections:
                    return ("isolate", node_id)
                return ("patch", node_id, vuln_id)
        return ("noop",)


def dispatch(env: TwinEnv, action: tuple) -> dict[str, Any]:
    kind = action[0]
    if kind == "patch":
        return env.blue_patch(action[1], action[2])
    if kind == "isolate":
        return env.blue_isolate(action[1])
    if kind == "noop":
        return {"ok": True}
    raise ValueError(f"unknown blue action: {action}")
