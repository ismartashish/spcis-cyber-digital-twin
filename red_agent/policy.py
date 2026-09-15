"""
red_agent.policy
=================

Baseline RED policy against digital_twin.env.TwinEnv.

`HeuristicRedPolicy` implements a simple, explainable tactic order —
scan known nodes, then exploit the highest-severity unpatched
vulnerability reachable, then pivot from any freshly compromised node —
which is enough to exercise the full loop (orchestrator, verification,
reporting) without requiring an RL training run.

`RandomRedPolicy` is a sanity-check baseline for reward-shaping tests
(§3 of docs/ARCHITECTURE.md warns that a red policy must never be
rewarded for un-reproducible or degenerate behavior — comparing a
trained policy's episode return against the random baseline is the
first regression test for that).

`build_rl_env()` at the bottom adapts TwinEnv into a flat, fixed-size
Gymnasium environment so an RL library (PPO, etc.) can be pointed at it;
see red_agent/train.py.
"""
from __future__ import annotations

import random
from typing import Any

from digital_twin.env import TwinEnv


class HeuristicRedPolicy:
    name = "heuristic_red_v0"

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def act(self, env: TwinEnv) -> tuple:
        """Return one action tuple, given full read access to env state
        (a heuristic policy is allowed to 'cheat' and look at env directly;
        an RL policy would only see env._observation())."""
        # 1) scan any known-but-unscanned node first (cheap recon)
        for node_id in sorted(env.red_known_nodes):
            node = env.topology.nodes[node_id]
            unpatched = [v for v in node.vulnerabilities if not v.patched]
            if unpatched and node_id not in env.isolated_nodes:
                # 2) exploit the highest-severity unpatched vuln we know about
                best = max(unpatched, key=lambda v: v.severity * v.exploitability)
                return ("exploit", node_id, best.vuln_id)

        # 3) nothing exploitable yet known -> scan a known node to expand the graph
        scannable = [n for n in env.red_known_nodes if n not in env.isolated_nodes]
        if scannable:
            return ("scan", self.rng.choice(scannable))

        # 4) try pivoting from a compromised node to expand reach
        compromised = [n for n, node in env.topology.nodes.items() if node.compromised]
        if compromised:
            src = self.rng.choice(compromised)
            candidates = [
                n for n, node in env.topology.nodes.items()
                if src in node.reachable_from and n not in env.red_known_nodes
            ]
            if candidates:
                return ("pivot", src, self.rng.choice(candidates))

        return ("noop",)


class RandomRedPolicy:
    name = "random_red_v0"

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def act(self, env: TwinEnv) -> tuple:
        choices: list[tuple] = []
        for node_id in env.red_known_nodes:
            if node_id in env.isolated_nodes:
                continue
            choices.append(("scan", node_id))
            node = env.topology.nodes[node_id]
            for v in node.vulnerabilities:
                if not v.patched:
                    choices.append(("exploit", node_id, v.vuln_id))
        if not choices:
            return ("noop",)
        return self.rng.choice(choices)


def dispatch(env: TwinEnv, action: tuple) -> dict[str, Any]:
    """Apply a red action tuple to the environment and return the result dict."""
    kind = action[0]
    if kind == "scan":
        return env.red_scan(action[1])
    if kind == "exploit":
        return env.red_exploit(action[1], action[2])
    if kind == "pivot":
        return env.red_pivot(action[1], action[2])
    if kind == "noop":
        return {"ok": True}
    raise ValueError(f"unknown red action: {action}")
