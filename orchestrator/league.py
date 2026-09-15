"""
orchestrator.league
====================

STUB for Phase 2 of docs/ARCHITECTURE.md (§8): league-based self-play,
where current red/blue agents periodically face a sampled mix of past
opponent checkpoints rather than only the latest version, to avoid
cyclic non-transitive strategies (AlphaStar/OpenAI Five lesson).

Not implemented — Phase 0/1 (orchestrator/arena.py) uses a single fixed
heuristic opponent. This file sketches the interface a real
implementation would fill in, so the rest of the codebase (arena,
reporting) has a stable shape to extend against.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Protocol


class Policy(Protocol):
    name: str
    def act(self, env) -> tuple: ...


@dataclass
class Checkpoint:
    policy: Policy
    generation: int
    win_rate_vs_league: float = 0.0


@dataclass
class League:
    """Population of past checkpoints for one side (red or blue)."""
    checkpoints: list[Checkpoint] = field(default_factory=list)

    def add(self, policy: Policy, generation: int) -> None:
        self.checkpoints.append(Checkpoint(policy=policy, generation=generation))

    def sample_opponent(self, rng: random.Random | None = None,
                         recent_bias: float = 0.5) -> Policy:
        """
        Sample an opponent checkpoint. `recent_bias` controls how much
        weight goes to the most recent checkpoints vs. the full history —
        a real implementation should tune this (and likely add
        prioritized fictitious self-play weighting by exploitability)
        rather than using the flat/linear scheme below.
        """
        rng = rng or random.Random()
        if not self.checkpoints:
            raise ValueError("league is empty — add at least one checkpoint")
        if rng.random() < recent_bias:
            return self.checkpoints[-1].policy
        return rng.choice(self.checkpoints).policy

    def promote_if_ready(self, candidate: Policy, generation: int,
                          win_rate_vs_league: float, threshold: float = 0.55) -> bool:
        """Add `candidate` to the league only if it beats the current
        league at better than `threshold` win rate over enough episodes
        (episode count / statistical significance check intentionally
        left to the caller — this stub only gates on the rate itself)."""
        if win_rate_vs_league >= threshold:
            self.add(candidate, generation)
            return True
        return False
