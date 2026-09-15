"""
verification/reachability_check.py

Reference illustration (per docs/ARCHITECTURE.md §4) of encoding a
network-reachability invariant as an SMT problem and checking it with
Z3, for the case where a hand-written Python predicate (as in
invariants.py) isn't expressive enough — e.g. "for every pair of nodes
(a, b) where a legitimate service dependency requires a -> b, there
must still exist SOME path after blue's proposed isolation/ACL changes."

This is illustrative reference code, not wired into the toy loop.
Requires the `z3-solver` package (see requirements-rl.txt).

Usage:
    python -m verification.reachability_check
"""
from __future__ import annotations

from typing import Iterable


def check_required_paths_preserved(
    edges_before: set[tuple[str, str]],
    isolated_nodes: set[str],
    required_paths: Iterable[tuple[str, str]],
) -> dict[str, bool]:
    """
    For each (src, dst) in required_paths, verify a path still exists
    in the graph after removing isolated_nodes and their edges.

    Uses Z3 to encode "reachable(dst)" via a least-fixed-point-style
    unrolling (bounded by node count) — overkill for this toy graph
    size, but this is the pattern that generalizes to the SMT-encoded
    IAM/network-policy checks a real deployment would run.
    """
    from z3 import Bool, Solver, Or, And, Implies, sat

    nodes = {n for edge in edges_before for n in edge} - isolated_nodes
    edges = {
        (a, b) for (a, b) in edges_before
        if a not in isolated_nodes and b not in isolated_nodes
    }

    results: dict[str, bool] = {}
    for src, dst in required_paths:
        if src in isolated_nodes or dst in isolated_nodes:
            results[f"{src}->{dst}"] = False
            continue

        s = Solver()
        reach = {n: Bool(f"reach_{n}") for n in nodes}
        s.add(reach[src] == True)  # noqa: E712
        for n in nodes:
            preds = [reach[a] for (a, b) in edges if b == n and a in reach]
            if n != src:
                s.add(Implies(Or(*preds) if preds else False, reach[n]))
        s.push()
        s.add(reach.get(dst, Bool("unknown")) == False)  # noqa: E712 -- try to prove unreachable
        unreachable_possible = s.check() == sat
        results[f"{src}->{dst}"] = not unreachable_possible
        s.pop()

    return results


if __name__ == "__main__":
    edges = {("internet", "web"), ("web", "api"), ("api", "db")}
    required = [("internet", "db")]
    print(check_required_paths_preserved(edges, isolated_nodes=set(), required_paths=required))
    print(check_required_paths_preserved(edges, isolated_nodes={"api"}, required_paths=required))
