"""
digital_twin.env
=================

An ABSTRACT, SIMULATED network environment for the red/blue self-play loop.

This is intentionally symbolic: nodes are dictionaries, "vulnerabilities"
are string CVE-style identifiers with numeric severity/exploitability
scores, and "exploiting" a vulnerability is a lookup against that data,
not real code execution. Swapping this module for a real IaC-derived
digital twin (per docs/ARCHITECTURE.md §5) is a separate, much larger
infrastructure project with its own isolation/containment requirements —
this class exists so the rest of the loop (agents, orchestrator,
verification, reporting) has something concrete and safe to run against.

The API loosely follows the Gymnasium (OpenAI Gym) convention
(reset / step) so it's easy to drop into stable-baselines3 or RLlib later.
"""
from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Any, Optional


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------

@dataclass
class Vulnerability:
    """A symbolic vulnerability record — data only, no exploit code."""
    vuln_id: str            # e.g. "CVE-2023-XXXX" or "MISCONFIG-IAM-01"
    vuln_class: str         # e.g. "sqli", "auth_bypass", "ssrf", "deser", "iam_overpermission"
    severity: float         # 0-10, CVSS-style
    exploitability: float   # 0-1, probability a competent attempt succeeds
    patched: bool = False


@dataclass
class Node:
    node_id: str
    role: str                       # e.g. "web", "api", "db", "auth", "crown_jewel"
    reachable_from: list[str] = field(default_factory=list)  # node_ids
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    compromised: bool = False
    is_crown_jewel: bool = False
    detection_sensitivity: float = 0.3   # baseline chance blue notices an attempt here


@dataclass
class Topology:
    name: str
    nodes: dict[str, Node]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Topology":
        nodes = {}
        for n in d["nodes"]:
            vulns = [Vulnerability(**v) for v in n.get("vulnerabilities", [])]
            nodes[n["node_id"]] = Node(
                node_id=n["node_id"],
                role=n["role"],
                reachable_from=n.get("reachable_from", []),
                vulnerabilities=vulns,
                is_crown_jewel=n.get("is_crown_jewel", False),
                detection_sensitivity=n.get("detection_sensitivity", 0.3),
            )
        return Topology(name=d.get("name", "unnamed"), nodes=nodes)


# --------------------------------------------------------------------------
# Environment
# --------------------------------------------------------------------------

class TwinEnv:
    """
    A simulated multi-host network for one red-vs-blue episode.

    Red actions:
        ("scan", node_id)
        ("exploit", node_id, vuln_id)
        ("pivot", from_node_id, to_node_id)

    Blue actions:
        ("patch", node_id, vuln_id)
        ("isolate", node_id)         # cuts reachability edges to this node
        ("noop",)

    Reward computation lives in orchestrator/arena.py, not here — this
    class only tracks and exposes ground-truth state plus an event log
    that the explainability layer turns into a human-readable report.
    """

    def __init__(self, topology: Topology, max_steps: int = 40, seed: Optional[int] = None):
        self.base_topology = topology
        self.max_steps = max_steps
        self.rng = random.Random(seed)
        self.reset()

    def reset(self) -> dict[str, Any]:
        self.topology = copy.deepcopy(self.base_topology)
        self.step_count = 0
        self.red_known_nodes: set[str] = set()
        self.isolated_nodes: set[str] = set()
        self.event_log: list[dict[str, Any]] = []
        self.done = False
        # red starts with knowledge of any internet-facing node
        for node in self.topology.nodes.values():
            if not node.reachable_from:  # no prerequisite = externally reachable
                self.red_known_nodes.add(node.node_id)
        return self._observation()

    def _observation(self) -> dict[str, Any]:
        return {
            "known_nodes": sorted(self.red_known_nodes),
            "compromised_nodes": sorted(
                n for n, node in self.topology.nodes.items() if node.compromised
            ),
            "step": self.step_count,
        }

    def _log(self, actor: str, action: tuple, result: dict[str, Any]) -> None:
        self.event_log.append(
            {"step": self.step_count, "actor": actor, "action": action, "result": result}
        )

    # ---- red actions -----------------------------------------------------

    def red_scan(self, node_id: str) -> dict[str, Any]:
        node = self.topology.nodes.get(node_id)
        if node is None or node_id not in self.red_known_nodes:
            result = {"ok": False, "reason": "node unknown or does not exist"}
        else:
            newly_discovered = [
                nb for nb, n in self.topology.nodes.items()
                if node_id in n.reachable_from and nb not in self.red_known_nodes
                and nb not in self.isolated_nodes
            ]
            self.red_known_nodes.update(newly_discovered)
            result = {
                "ok": True,
                "vulnerabilities": [v.vuln_id for v in node.vulnerabilities if not v.patched],
                "newly_discovered_nodes": newly_discovered,
            }
        self._log("red", ("scan", node_id), result)
        return result

    def red_exploit(self, node_id: str, vuln_id: str) -> dict[str, Any]:
        node = self.topology.nodes.get(node_id)
        detected = False
        if node is None or node_id not in self.red_known_nodes or node_id in self.isolated_nodes:
            result = {"ok": False, "reason": "node unreachable/unknown/isolated"}
        else:
            vuln = next((v for v in node.vulnerabilities if v.vuln_id == vuln_id), None)
            if vuln is None or vuln.patched:
                result = {"ok": False, "reason": "vulnerability absent or already patched"}
            else:
                success = self.rng.random() < vuln.exploitability
                detected = self.rng.random() < node.detection_sensitivity
                if success:
                    node.compromised = True
                result = {
                    "ok": success,
                    "detected": detected,
                    "severity": vuln.severity,
                    "vuln_class": vuln.vuln_class,
                    "is_crown_jewel": node.is_crown_jewel,
                }
        self._log("red", ("exploit", node_id, vuln_id), result)
        return result

    def red_pivot(self, from_node: str, to_node: str) -> dict[str, Any]:
        src = self.topology.nodes.get(from_node)
        if src is None or not src.compromised:
            result = {"ok": False, "reason": "source node not compromised"}
        elif to_node in self.isolated_nodes:
            result = {"ok": False, "reason": "target isolated"}
        elif from_node not in self.topology.nodes.get(to_node, Node("", "")).reachable_from:
            result = {"ok": False, "reason": "no network path"}
        else:
            self.red_known_nodes.add(to_node)
            result = {"ok": True}
        self._log("red", ("pivot", from_node, to_node), result)
        return result

    # ---- blue actions ------------------------------------------------------

    def blue_patch(self, node_id: str, vuln_id: str) -> dict[str, Any]:
        node = self.topology.nodes.get(node_id)
        if node is None:
            result = {"ok": False, "reason": "no such node"}
        else:
            vuln = next((v for v in node.vulnerabilities if v.vuln_id == vuln_id), None)
            if vuln is None:
                result = {"ok": False, "reason": "no such vulnerability"}
            else:
                vuln.patched = True
                result = {"ok": True}
        self._log("blue", ("patch", node_id, vuln_id), result)
        return result

    def blue_isolate(self, node_id: str) -> dict[str, Any]:
        self.isolated_nodes.add(node_id)
        self._log("blue", ("isolate", node_id), {"ok": True})
        return {"ok": True}

    # ---- episode control ----------------------------------------------------

    def tick(self) -> bool:
        """Advance the step counter; returns True if episode is over."""
        self.step_count += 1
        crown_jewel_owned = any(
            n.compromised and n.is_crown_jewel for n in self.topology.nodes.values()
        )
        self.done = crown_jewel_owned or self.step_count >= self.max_steps
        return self.done

    def summary(self) -> dict[str, Any]:
        return {
            "topology": self.topology.name,
            "steps_taken": self.step_count,
            "compromised_nodes": [n for n, node in self.topology.nodes.items() if node.compromised],
            "crown_jewel_compromised": any(
                n.compromised and n.is_crown_jewel for n in self.topology.nodes.values()
            ),
            "patched_vulns": [
                v.vuln_id for node in self.topology.nodes.values() for v in node.vulnerabilities if v.patched
            ],
            "isolated_nodes": sorted(self.isolated_nodes),
            "event_log": self.event_log,
        }
