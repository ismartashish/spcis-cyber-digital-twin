"""
orchestrator.arena
===================

The episode loop described in docs/ARCHITECTURE.md §3/§4/§8: runs red
vs. blue for one or more episodes against a topology, computes rewards
(including the reproducibility gate and the invariant-check gate), and
writes a run directory that explainability/report.py turns into a
human-readable report.

This is Phase 0/1 of the roadmap (heuristic agents, single fixed
opponent) — the league/self-play population manager described in §8 is
sketched in `orchestrator/league.py` as a stub for a later phase.

Usage:
    python -m orchestrator.arena --episodes 5 --config configs/twin_topology.yaml
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from dataclasses import asdict, dataclass

import yaml

from digital_twin.env import Topology, TwinEnv
from red_agent.policy import HeuristicRedPolicy, dispatch as red_dispatch
from blue_agent.policy import HeuristicBluePolicy, dispatch as blue_dispatch
from verification import invariants


@dataclass
class RewardBreakdown:
    red_reward: float = 0.0
    blue_reward: float = 0.0
    red_events: list = None
    blue_events: list = None

    def __post_init__(self):
        self.red_events = self.red_events or []
        self.blue_events = self.blue_events or []


def load_topology(path: str) -> Topology:
    with open(path, encoding="utf-8") as f:
        d = yaml.safe_load(f)
    return Topology.from_dict(d)


def run_episode(topology: Topology, red_policy, blue_policy, max_steps: int, seed: int) -> dict:
    env = TwinEnv(topology, max_steps=max_steps, seed=seed)
    rewards = RewardBreakdown()

    while True:
        # --- red turn ---
        red_action = red_policy.act(env)
        red_result = red_dispatch(env, red_action)

        if red_action[0] == "exploit" and red_result.get("ok"):
            # Reproducibility gate (docs/ARCHITECTURE.md §3): only reward a
            # compromise if it is replayable — i.e. we have the concrete
            # action + resulting state diff recorded in the event log.
            # Here that's guaranteed by construction (TwinEnv logs every
            # action deterministically given the seed), so the gate is
            # represented as an explicit assertion rather than a no-op,
            # to keep the requirement visible in the code.
            assert env.event_log, "reward claimed with no reproducible event log — refusing credit"
            reward = red_result.get("severity", 0.0)
            if red_result.get("is_crown_jewel"):
                reward += 10.0
            if red_result.get("detected"):
                reward -= 1.0  # stealth penalty
            rewards.red_reward += reward
            rewards.red_events.append({"action": red_action, "result": red_result, "reward": reward})

        # --- blue turn ---
        blue_action = blue_policy.act(env)

        # Invariant gate (docs/ARCHITECTURE.md §4): a blue action is only
        # credited if the resulting state still satisfies STATE_INVARIANTS.
        # We speculatively apply, check, and roll back if it fails.
        import copy
        pre_state = copy.deepcopy(env.topology), set(env.isolated_nodes)
        blue_result = blue_dispatch(env, blue_action)
        check_results = invariants.check_state(env)

        if invariants.all_passed(check_results):
            if blue_action[0] in ("patch", "isolate") and blue_result.get("ok"):
                reward = 2.0 if blue_action[0] == "patch" else 1.0
                rewards.blue_reward += reward
                rewards.blue_events.append(
                    {"action": blue_action, "result": blue_result, "reward": reward,
                     "invariant_checks": [asdict(r) for r in check_results]}
                )
        else:
            # roll back: invariant violation means this action is not credited
            # and not applied (mirrors "candidate patch rejected, PR not opened")
            env.topology, env.isolated_nodes = pre_state
            rewards.blue_reward -= 5.0  # -R_break
            rewards.blue_events.append(
                {"action": blue_action, "result": {"ok": False, "reason": "invariant violation"},
                 "reward": -5.0, "invariant_checks": [asdict(r) for r in check_results]}
            )

        if env.tick():
            break

    summary = env.summary()
    summary["red_reward"] = rewards.red_reward
    summary["blue_reward"] = rewards.blue_reward
    summary["red_reward_events"] = rewards.red_events
    summary["blue_reward_events"] = rewards.blue_events
    summary["red_policy"] = getattr(red_policy, "name", red_policy.__class__.__name__)
    summary["blue_policy"] = getattr(blue_policy, "name", blue_policy.__class__.__name__)
    summary["seed"] = seed
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/twin_topology.yaml")
    ap.add_argument("--episodes", type=int, default=5)
    ap.add_argument("--max-steps", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--run-dir", default=None)
    args = ap.parse_args()

    topology = load_topology(args.config)
    red = HeuristicRedPolicy(seed=args.seed)
    blue = HeuristicBluePolicy()

    run_dir = args.run_dir or f"runs/{int(time.time())}"
    os.makedirs(run_dir, exist_ok=True)
    latest_link = "runs/latest"
    try:
        if os.path.islink(latest_link) or os.path.exists(latest_link):
            if os.path.islink(latest_link) or os.path.isfile(latest_link):
                os.remove(latest_link)
            else:
                shutil.rmtree(latest_link)
        os.symlink(os.path.abspath(run_dir), latest_link)
    except OSError:
        # Symlinks need admin/Developer Mode on Windows — fall back to a
        # plain pointer file so `--run-dir runs/latest` still works.
        with open(latest_link, "w", encoding="utf-8") as f:
            f.write(os.path.abspath(run_dir))

    episodes = []
    for ep in range(args.episodes):
        summary = run_episode(topology, red, blue, args.max_steps, seed=args.seed + ep)
        episodes.append(summary)
        print(
            f"[episode {ep}] red_reward={summary['red_reward']:.2f} "
            f"blue_reward={summary['blue_reward']:.2f} "
            f"crown_jewel_compromised={summary['crown_jewel_compromised']}"
        )
        with open(os.path.join(run_dir, f"episode_{ep}.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

    with open(os.path.join(run_dir, "run_summary.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "n_episodes": len(episodes),
                "avg_red_reward": sum(e["red_reward"] for e in episodes) / len(episodes),
                "avg_blue_reward": sum(e["blue_reward"] for e in episodes) / len(episodes),
                "crown_jewel_compromise_rate": sum(e["crown_jewel_compromised"] for e in episodes) / len(episodes),
            },
            f, indent=2,
        )
    print(f"\nRun written to {run_dir}")


if __name__ == "__main__":
    main()
