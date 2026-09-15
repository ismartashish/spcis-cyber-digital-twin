"""
Tests for the digital-twin environment.

Run:

    python -m pytest tests/ -q
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
        )
    ),
)

from digital_twin.env import Topology, TwinEnv


def make_test_topology() -> Topology:

    return Topology.from_dict(
        {
            "name": "test-topo",

            "nodes": [

                {
                    "node_id": "web",
                    "role": "web",
                    "reachable_from": [],

                    "vulnerabilities": [

                        {
                            "vuln_id": "V1",
                            "vuln_class": "sqli",
                            "severity": 5.0,
                            "exploitability": 1.0,
                        }

                    ],
                },

                {
                    "node_id": "db",
                    "role": "db",
                    "reachable_from": ["web"],
                    "is_crown_jewel": True,

                    "vulnerabilities": [

                        {
                            "vuln_id": "V2",
                            "vuln_class": "priv_esc",
                            "severity": 9.0,
                            "exploitability": 1.0,
                        }

                    ],
                },

            ],
        }
    )


def test_reset_gives_red_the_internet_facing_node():

    env = TwinEnv(
        make_test_topology(),
        seed=1,
    )

    assert (
        "web"
        in env.red_known_nodes
    )

    assert (
        "db"
        not in env.red_known_nodes
    )


def test_exploit_with_exploitability_1_always_succeeds():

    env = TwinEnv(
        make_test_topology(),
        seed=1,
    )

    result = env.red_exploit(
        "web",
        "V1",
    )

    assert result["ok"] is True

    assert (
        env.topology.nodes["web"].compromised
        is True
    )


def test_pivot_requires_source_compromised():

    env = TwinEnv(
        make_test_topology(),
        seed=1,
    )

    # Cannot pivot before compromise.
    result = env.red_pivot(
        "web",
        "db",
    )

    assert result["ok"] is False

    # Compromise web.
    env.red_exploit(
        "web",
        "V1",
    )

    # Pivot should now succeed.
    result = env.red_pivot(
        "web",
        "db",
    )

    assert result["ok"] is True

    assert (
        "db"
        in env.red_known_nodes
    )


def test_patch_prevents_future_exploit():

    env = TwinEnv(
        make_test_topology(),
        seed=1,
    )

    env.blue_patch(
        "web",
        "V1",
    )

    result = env.red_exploit(
        "web",
        "V1",
    )

    assert result["ok"] is False

    assert (
        result["reason"]
        == "vulnerability absent or already patched"
    )


def test_episode_ends_on_crown_jewel_or_max_steps():

    env = TwinEnv(
        make_test_topology(),
        max_steps=5,
        seed=1,
    )

    done = False

    for _ in range(10):

        if done:
            break

        env.red_exploit(
            "web",
            "V1",
        )

        env.red_pivot(
            "web",
            "db",
        )

        env.red_exploit(
            "db",
            "V2",
        )

        done = env.tick()

    assert (
        env.summary()[
            "crown_jewel_compromised"
        ]
        is True
    )


if __name__ == "__main__":

    pytest.main(
        [
            __file__,
            "-q",
        ]
    )