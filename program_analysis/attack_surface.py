"""
program_analysis.attack_surface
================================

Stub for the "white-box" feed described in docs/ARCHITECTURE.md §6:
static/dependency analysis results that seed red's attack-graph state
with candidate entry points, instead of red starting purely black-box.

This module does NOT perform real static analysis or fuzzing — it
defines the *interface and data shape* that a real integration (Semgrep/
CodeQL for SAST, an SBOM diff against a CVE feed, AFL++/angr for
dynamic analysis) would populate, and a small illustrative function
that turns a dependency manifest into the same Vulnerability records
digital_twin.env consumes, so the two layers compose cleanly.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AttackSurfaceHint:
    node_id: str
    hint_type: str          # "known_vulnerable_dependency" | "taint_sink" | "iam_overpermission" | ...
    detail: str
    confidence: float       # 0-1, how much to trust this static signal


def hints_from_dependency_manifest(node_id: str, dependencies: dict[str, str],
                                    cve_feed: dict[str, list[dict]]) -> list[AttackSurfaceHint]:
    """
    `dependencies`: {"package_name": "installed_version"}
    `cve_feed`: {"package_name": [{"cve_id": ..., "affected_below": "x.y.z",
                                    "severity": float}, ...]}

    A real implementation would pull `cve_feed` from an actual SBOM/CVE
    database (e.g. OSV, GitHub Advisory DB) — this function just shows
    the shape of turning "package X at version Y" into structured hints
    that feed red's prior knowledge, which is the point being illustrated.
    """
    hints: list[AttackSurfaceHint] = []
    for pkg, version in dependencies.items():
        for entry in cve_feed.get(pkg, []):
            # naive string compare placeholder — a real implementation
            # needs proper semver comparison.
            if version < entry["affected_below"]:
                hints.append(
                    AttackSurfaceHint(
                        node_id=node_id,
                        hint_type="known_vulnerable_dependency",
                        detail=f"{pkg}=={version} affected by {entry['cve_id']}",
                        confidence=0.9,
                    )
                )
    return hints


def hints_to_vulnerabilities(hints: list[AttackSurfaceHint]):
    """Adapter: turn AttackSurfaceHints into digital_twin.env.Vulnerability
    records so they can be merged into a Topology built from real scan
    data rather than hand-authored YAML."""
    from digital_twin.env import Vulnerability

    out = []
    for h in hints:
        if h.hint_type == "known_vulnerable_dependency":
            cve_id = h.detail.split("affected by ")[-1]
            out.append(
                Vulnerability(
                    vuln_id=cve_id,
                    vuln_class="known_cve_dependency",
                    severity=7.5,
                    exploitability=h.confidence,
                )
            )
    return out
