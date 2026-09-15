"""
verification.invariants
========================

The formal-methods gate described in docs/ARCHITECTURE.md §4: every blue
action is checked against a set of system invariants BEFORE it is
allowed to count for reward or be marked "applied". A blue action that
fails an invariant is logged but rolled back / not credited — this is
the mechanism that stops blue from "winning" by e.g. isolating every
node in the network.

This module implements the invariants as plain Python predicates for
the toy environment (fast, dependency-free, good for unit tests and CI).
`verification/policy.rego` and `verification/reachability.smt2` in this
same directory show what the equivalent checks look like expressed as
policy-as-code (OPA/Rego) and as an SMT reachability encoding (Z3) —
the two tools named in the architecture doc for a real deployment,
included here for reference/illustration rather than wired into the
toy loop.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from digital_twin.env import TwinEnv

MIN_REACHABLE_ROLES = {"web", "api"}  # these roles must stay reachable from the internet-facing edge


@dataclass
class InvariantResult:
    name: str
    passed: bool
    detail: str


def check_no_full_isolation(env: TwinEnv) -> InvariantResult:
    """Blue must never isolate every node — that's not a fix, it's an outage."""
    total = len(env.topology.nodes)
    isolated = len(env.isolated_nodes)
    passed = isolated < total
    return InvariantResult(
        "no_full_isolation", passed,
        f"{isolated}/{total} nodes isolated" if not passed else "ok",
    )


def check_web_tier_reachable(env: TwinEnv) -> InvariantResult:
    """Any node with role in MIN_REACHABLE_ROLES must not be isolated —
    stands in for 'legitimate traffic must still reach the app.'"""
    offending = [
        n for n, node in env.topology.nodes.items()
        if node.role in MIN_REACHABLE_ROLES and n in env.isolated_nodes
    ]
    passed = not offending
    return InvariantResult(
        "web_tier_reachable", passed,
        f"isolated web/api nodes: {offending}" if offending else "ok",
    )


def check_no_redundant_patch(env: TwinEnv, node_id: str, vuln_id: str) -> InvariantResult:
    """A patch action targeting an already-patched vuln is a wasted/no-op
    action — flagged so the reward function can decline to credit it."""
    node = env.topology.nodes.get(node_id)
    vuln = next((v for v in node.vulnerabilities if v.vuln_id == vuln_id), None) if node else None
    passed = vuln is not None and not vuln.patched
    return InvariantResult(
        "no_redundant_patch", passed,
        "ok" if passed else f"{vuln_id} on {node_id} already patched or missing",
    )


# Registry of invariants that must hold on every environment state,
# regardless of which specific blue action just ran.
STATE_INVARIANTS: list[Callable[[TwinEnv], InvariantResult]] = [
    check_no_full_isolation,
    check_web_tier_reachable,
]


def check_state(env: TwinEnv) -> list[InvariantResult]:
    return [inv(env) for inv in STATE_INVARIANTS]


def all_passed(results: list[InvariantResult]) -> bool:
    return all(r.passed for r in results)
