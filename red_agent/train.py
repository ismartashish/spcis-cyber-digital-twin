"""
red_agent.train
===============

Maskable PPO red-agent training environment for the SPCIS digital twin.

Actions:
    1. EXPLOIT(node, vulnerability)
    2. SCAN(node)
    3. PIVOT(source, target)

Features:
    - True action masking using sb3-contrib MaskablePPO
    - Fresh topology for every episode
    - Reward shaping focused on crown-jewel compromise
    - Topology-aware observations
    - Positive normalized entropy metric: 0.0 -> 1.0
    - Native SB3 entropy_loss remains untouched/correct
    - Explicit exploit / pivot / scan statistics
    - Deterministic evaluation
    - Fixed learning rate
    - No progress-bar dependency

Install:
    python -m pip install sb3-contrib

Run:
    python -m red_agent.train ^
        --config configs/twin_topology.yaml ^
        --timesteps 100000 ^
        --eval-episodes 100
"""

from __future__ import annotations

import argparse
import copy
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import yaml

from stable_baselines3.common.callbacks import BaseCallback
from digital_twin.env import Topology, TwinEnv
from blue_agent.policy import (
    HeuristicBluePolicy,
    dispatch as blue_dispatch,
)


try:
    import gymnasium as gym
    from gymnasium import spaces

    _GYM_BASE = gym.Env

except ImportError:  # pragma: no cover
    gym = None
    spaces = None
    _GYM_BASE = object


# ============================================================
# ENTROPY MONITOR
# ============================================================

class EntropyMonitorCallback(BaseCallback):
    """
    Logs a positive normalized entropy score.

    train/entropy_score:
        0.0 = nearly deterministic policy
        1.0 = maximum entropy across the complete action space

    train/policy_entropy:
        Raw policy entropy.

    IMPORTANT:
        SB3's native train/entropy_loss is NOT modified.

        In PPO:
            entropy_loss = -policy_entropy

        Therefore native entropy_loss is expected to be
        negative. We keep it that way and add our own
        positive metric for easier monitoring.
    """

    def __init__(self, verbose: int = 0):
        super().__init__(verbose)

    def _on_step(self) -> bool:
        return True

    def _on_rollout_end(self) -> None:
        if not hasattr(self.model, "policy"):
            return

        try:
            observations = self.model.rollout_buffer.observations

            if observations is None:
                return

            observations = np.asarray(observations)

            if observations.size == 0:
                return

            # Expected shape from PPO:
            #   (n_steps, n_envs, obs_dim)
            #
            # Flatten everything except the observation dimension.
            obs_dim = observations.shape[-1]
            flat_observations = observations.reshape(-1, obs_dim)

            # Keep callback inexpensive.
            max_samples = 2048

            if len(flat_observations) > max_samples:
                flat_observations = flat_observations[:max_samples]

            obs_tensor, _ = self.model.policy.obs_to_tensor(
                flat_observations
            )

            with torch.no_grad():
                distribution = self.model.policy.get_distribution(
                    obs_tensor
                )

                entropy_tensor = (
                    distribution.distribution.entropy()
                )

                actual_entropy = float(
                    entropy_tensor.mean().detach().cpu().item()
                )

            # Maximum entropy of a uniform categorical
            # distribution over N actions:
            #
            #       H_max = log(N)
            #
            action_space = self.training_env.action_space
            n_actions = int(action_space.n)

            max_entropy = math.log(
                max(2, n_actions)
            )

            normalized_entropy = (
                actual_entropy / max_entropy
                if max_entropy > 0.0
                else 0.0
            )

            normalized_entropy = float(
                np.clip(
                    normalized_entropy,
                    0.0,
                    1.0,
                )
            )

            # Positive 0..1 metric.
            self.logger.record(
                "train/entropy_score",
                normalized_entropy,
            )

            # Raw entropy for diagnostics.
            self.logger.record(
                "train/policy_entropy",
                actual_entropy,
            )

        except Exception:
            # Never allow monitoring code to interrupt training.
            pass


# ============================================================
# TOPOLOGY
# ============================================================

def load_topology(path: str) -> Topology:
    """Load topology from YAML."""

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        data = yaml.safe_load(file)

    return Topology.from_dict(data)


# ============================================================
# ACTION TYPES
# ============================================================

@dataclass(frozen=True)
class ExploitAction:
    node_id: str
    vuln_slot: int


@dataclass(frozen=True)
class ScanAction:
    node_id: str


@dataclass(frozen=True)
class PivotAction:
    source_id: str
    target_id: str


# ============================================================
# ENVIRONMENT
# ============================================================

class FlatRedGymEnv(_GYM_BASE):
    """
    Gymnasium environment for the red attacker.

    Observation per node:

        0 = known
        1 = compromised
        2 = isolated
        3 = maximum unpatched vulnerability severity
        4 = can act as pivot source
        5 = reachable unknown target ratio

    Action space:

        EXPLOIT(node, vulnerability)
        SCAN(node)
        PIVOT(source, target)
    """

    def __init__(
        self,
        topology: Topology,
        max_vulns_per_node: int = 4,
        max_steps: int = 40,
    ) -> None:

        if gym is None:
            raise ImportError(
                "gymnasium is required.\n"
                "Run:\n"
                "python -m pip install -r requirements-rl.txt"
            )

        super().__init__()

        self.original_topology = topology

        self.node_ids = sorted(
            topology.nodes.keys()
        )

        self.n_nodes = len(
            self.node_ids
        )

        self.node_index = {
            node_id: index
            for index, node_id
            in enumerate(self.node_ids)
        }

        self.max_vulns = max_vulns_per_node
        self.max_steps = max_steps

        self.blue = HeuristicBluePolicy()

        self.env: TwinEnv | None = None

        # --------------------------------------------------------
        # ACTION TABLE
        # --------------------------------------------------------

        self.actions: list[
            ExploitAction
            | ScanAction
            | PivotAction
        ] = []

        # --------------------------------------------------------
        # EXPLOIT ACTIONS
        # --------------------------------------------------------

        for node_id in self.node_ids:

            for vuln_slot in range(
                self.max_vulns
            ):

                self.actions.append(
                    ExploitAction(
                        node_id=node_id,
                        vuln_slot=vuln_slot,
                    )
                )

        # --------------------------------------------------------
        # SCAN ACTIONS
        # --------------------------------------------------------

        for node_id in self.node_ids:

            self.actions.append(
                ScanAction(
                    node_id=node_id
                )
            )

        # --------------------------------------------------------
        # PIVOT ACTIONS
        # --------------------------------------------------------

        for source_id in self.node_ids:

            for target_id in self.node_ids:

                if source_id == target_id:
                    continue

                self.actions.append(
                    PivotAction(
                        source_id=source_id,
                        target_id=target_id,
                    )
                )

        self.action_space = spaces.Discrete(
            len(self.actions)
        )

        # --------------------------------------------------------
        # OBSERVATION
        # --------------------------------------------------------

        self.features_per_node = 6

        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(
                self.n_nodes
                * self.features_per_node,
            ),
            dtype=np.float32,
        )

    # ========================================================
    # OBSERVATION
    # ========================================================

    def _obs(self) -> np.ndarray:

        if self.env is None:
            raise RuntimeError(
                "Environment has not been reset."
            )

        features: list[float] = []

        for node_id in self.node_ids:

            node = (
                self.env.topology.nodes[
                    node_id
                ]
            )

            # ------------------------------------------------
            # KNOWN
            # ------------------------------------------------

            known = (
                1.0
                if node_id
                in self.env.red_known_nodes
                else 0.0
            )

            # ------------------------------------------------
            # COMPROMISED
            # ------------------------------------------------

            compromised = (
                1.0
                if node.compromised
                else 0.0
            )

            # ------------------------------------------------
            # ISOLATED
            # ------------------------------------------------

            isolated = (
                1.0
                if node_id
                in self.env.isolated_nodes
                else 0.0
            )

            # ------------------------------------------------
            # MAX VULNERABILITY SEVERITY
            # ------------------------------------------------

            unpatched = [
                vuln.severity
                for vuln
                in node.vulnerabilities
                if not vuln.patched
            ]

            max_severity = (
                max(unpatched) / 10.0
                if unpatched
                else 0.0
            )

            max_severity = float(
                np.clip(
                    max_severity,
                    0.0,
                    1.0,
                )
            )

            # ------------------------------------------------
            # CAN PIVOT
            # ------------------------------------------------

            can_pivot = (
                1.0
                if compromised
                and not isolated
                else 0.0
            )

            # ------------------------------------------------
            # REACHABLE UNKNOWN TARGET RATIO
            # ------------------------------------------------

            reachable_unknown = 0

            if compromised:

                for target_id in self.node_ids:

                    if target_id == node_id:
                        continue

                    if (
                        target_id
                        not in self.env.red_known_nodes
                        and self._is_reachable(
                            node_id,
                            target_id,
                        )
                    ):
                        reachable_unknown += 1

            reachable_ratio = (
                reachable_unknown
                / max(
                    1,
                    self.n_nodes - 1,
                )
            )

            reachable_ratio = float(
                np.clip(
                    reachable_ratio,
                    0.0,
                    1.0,
                )
            )

            features.extend(
                [
                    known,
                    compromised,
                    isolated,
                    max_severity,
                    can_pivot,
                    reachable_ratio,
                ]
            )

        return np.asarray(
            features,
            dtype=np.float32,
        )

    # ========================================================
    # GRAPH / REACHABILITY
    # ========================================================

    def _is_reachable(
        self,
        source_id: str,
        target_id: str,
    ) -> bool:
        """
        Determine whether target_id can be discovered
        from source_id.

        SPCIS topology data commonly stores the relation
        on the destination node via `reachable_from`.

        Example:

            db.reachable_from = ["web"]

        means:

            web -> db

        We therefore first check the target's
        `reachable_from` list.

        A fallback check for the source node is retained
        for topologies that encode the relation in the
        opposite direction.
        """

        if self.env is None:
            return False

        source_node = (
            self.env.topology.nodes[
                source_id
            ]
        )

        target_node = (
            self.env.topology.nodes[
                target_id
            ]
        )

        # ----------------------------------------------------
        # Primary SPCIS convention:
        #
        # target.reachable_from contains source
        # ----------------------------------------------------

        target_reachable_from = getattr(
            target_node,
            "reachable_from",
            [],
        )

        if source_id in target_reachable_from:
            return True

        # ----------------------------------------------------
        # Fallback for topologies that encode:
        #
        # source.reachable_from contains target
        # ----------------------------------------------------

        source_reachable_to = getattr(
            source_node,
            "reachable_from",
            [],
        )

        if target_id in source_reachable_to:
            return True

        return False

    # ========================================================
    # ACTION MASK
    # ========================================================

    def action_masks(self) -> np.ndarray:
        """
        Return a boolean action mask.

        True:
            valid action

        False:
            invalid action

        MaskablePPO uses this to prevent selection of
        impossible actions.
        """

        if self.env is None:
            raise RuntimeError(
                "Environment has not been reset."
            )

        mask = np.zeros(
            len(self.actions),
            dtype=bool,
        )

        for index, action in enumerate(
            self.actions
        ):

            # =================================================
            # EXPLOIT
            # =================================================

            if isinstance(
                action,
                ExploitAction,
            ):

                node_id = action.node_id

                # Unknown node cannot be exploited.
                if (
                    node_id
                    not in self.env.red_known_nodes
                ):
                    continue

                node = (
                    self.env.topology.nodes[
                        node_id
                    ]
                )

                unpatched = [
                    vuln
                    for vuln
                    in node.vulnerabilities
                    if not vuln.patched
                ]

                # Invalid vulnerability slot.
                if (
                    action.vuln_slot
                    >= len(unpatched)
                ):
                    continue

                # Isolated nodes cannot be attacked.
                if (
                    node_id
                    in self.env.isolated_nodes
                ):
                    continue

                mask[index] = True

            # =================================================
            # SCAN
            # =================================================

            elif isinstance(
                action,
                ScanAction,
            ):

                node_id = action.node_id

                # Only known/non-isolated nodes.
                if (
                    node_id
                    in self.env.red_known_nodes
                    and node_id
                    not in self.env.isolated_nodes
                ):
                    mask[index] = True

            # =================================================
            # PIVOT
            # =================================================

            elif isinstance(
                action,
                PivotAction,
            ):

                source = action.source_id
                target = action.target_id

                # Source must be known.
                if (
                    source
                    not in self.env.red_known_nodes
                ):
                    continue

                source_node = (
                    self.env.topology.nodes[
                        source
                    ]
                )

                # Source must be compromised.
                if not source_node.compromised:
                    continue

                # Isolated source cannot pivot.
                if (
                    source
                    in self.env.isolated_nodes
                ):
                    continue

                # Target already known => no discovery
                # benefit from this pivot.
                if (
                    target
                    in self.env.red_known_nodes
                ):
                    continue

                # Target must be reachable.
                if not self._is_reachable(
                    source,
                    target,
                ):
                    continue

                mask[index] = True

        # ----------------------------------------------------
        # SAFETY FALLBACK
        # ----------------------------------------------------

        if not mask.any():

            # Permit a valid scan on a known node.
            for index, action in enumerate(
                self.actions
            ):

                if isinstance(
                    action,
                    ScanAction,
                ):

                    if (
                        action.node_id
                        in self.env.red_known_nodes
                        and action.node_id
                        not in self.env.isolated_nodes
                    ):

                        mask[index] = True
                        break

        return mask

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict | None = None,
    ):

        super().reset(
            seed=seed
        )

        # Fresh topology for every episode.
        self.env = TwinEnv(
            copy.deepcopy(
                self.original_topology
            ),
            max_steps=self.max_steps,
            seed=seed,
        )

        return self._obs(), {}

    # ========================================================
    # STEP
    # ========================================================

    def step(
        self,
        action: int,
    ):

        if self.env is None:
            raise RuntimeError(
                "Environment has not been reset."
            )

        action = int(action)

        if not self.action_space.contains(
            action
        ):
            raise ValueError(
                f"Invalid action: {action}"
            )

        # Enforce mask even if external caller
        # provides an invalid action.
        mask = self.action_masks()

        if not mask[action]:

            return (
                self._obs(),
                -0.50,
                False,
                False,
                {
                    "action_type":
                        "invalid_masked_action",
                    "raw_result": {
                        "ok": False,
                        "reason":
                            "invalid action",
                    },
                    "red_reward":
                        -0.50,
                },
            )

        selected = self.actions[
            action
        ]

        reward = 0.0

        result: dict[str, Any] = {
            "ok": False
        }

        action_type = "unknown"

        # ====================================================
        # EXPLOIT
        # ====================================================

        if isinstance(
            selected,
            ExploitAction,
        ):

            action_type = "exploit"

            node_id = selected.node_id

            node = (
                self.env.topology.nodes[
                    node_id
                ]
            )

            unpatched = [
                vuln
                for vuln
                in node.vulnerabilities
                if not vuln.patched
            ]

            vuln = unpatched[
                selected.vuln_slot
            ]

            was_compromised = bool(
                node.compromised
            )

            result = (
                self.env.red_exploit(
                    node_id,
                    vuln.vuln_id,
                )
            )

            # ------------------------------------------------
            # SUCCESSFUL FIRST COMPROMISE
            # ------------------------------------------------

            if (
                result.get(
                    "ok",
                    False,
                )
                and not was_compromised
            ):

                severity = float(
                    result.get(
                        "severity",
                        0.0,
                    )
                )

                # Strong reward for actual progress.
                reward += (
                    5.0 + severity
                )

                # Crown jewel objective.
                if result.get(
                    "is_crown_jewel",
                    False,
                ):

                    reward += 50.0

                    action_type = (
                        "crown_jewel_exploit"
                    )

            # ------------------------------------------------
            # DETECTION
            # ------------------------------------------------

            if result.get(
                "detected",
                False,
            ):
                reward -= 1.0

            # ------------------------------------------------
            # FAILED EXPLOIT
            # ------------------------------------------------

            if not result.get(
                "ok",
                False,
            ):
                reward -= 0.10

        # ====================================================
        # SCAN
        # ====================================================

        elif isinstance(
            selected,
            ScanAction,
        ):

            action_type = "scan"

            node_id = selected.node_id

            result = (
                self.env.red_scan(
                    node_id
                )
            )

            # ------------------------------------------------
            # IMPORTANT
            #
            # Scanning is information gathering.
            # It does NOT receive positive reward.
            #
            # This prevents:
            #
            #     scan -> scan -> scan -> ...
            #
            # from becoming a reward-hacking strategy.
            # ------------------------------------------------

            if result.get(
                "ok",
                False,
            ):

                reward -= 0.02

            else:

                reward -= 0.10

        # ====================================================
        # PIVOT
        # ====================================================

        elif isinstance(
            selected,
            PivotAction,
        ):

            action_type = "pivot"

            source = selected.source_id
            target = selected.target_id

            target_was_known = (
                target
                in self.env.red_known_nodes
            )

            result = (
                self.env.red_pivot(
                    source,
                    target,
                )
            )

            if result.get(
                "ok",
                False,
            ):

                # New discovery is strategically useful.
                if not target_was_known:
                    reward += 3.0

                else:
                    reward += 0.25

            else:

                reward -= 0.25

        # ====================================================
        # BLUE DEFENDER
        # ====================================================

        blue_action = (
            self.blue.act(
                self.env
            )
        )

        blue_dispatch(
            self.env,
            blue_action,
        )

        # ====================================================
        # TICK
        # ====================================================

        terminated = bool(
            self.env.tick()
        )

        truncated = False

        # ====================================================
        # INFO
        # ====================================================

        summary = (
            self.env.summary()
        )

        info: dict[str, Any] = {

            "raw_result":
                result,

            "red_reward":
                float(reward),

            "action_type":
                action_type,

            "crown_jewel_compromised":
                bool(
                    summary.get(
                        "crown_jewel_compromised",
                        False,
                    )
                ),
        }

        return (
            self._obs(),
            float(reward),
            terminated,
            truncated,
            info,
        )


# ============================================================
# EVALUATION
# ============================================================

def evaluate_policy(
    model,
    env: FlatRedGymEnv,
    episodes: int = 100,
    seed: int = 12345,
) -> dict[str, float]:

    rewards: list[float] = []

    positive_rewards = 0
    crown_jewel_successes = 0

    pivot_attempts = 0
    successful_pivots = 0

    exploit_attempts = 0
    successful_exploits = 0

    scan_attempts = 0
    successful_scans = 0

    episode_lengths: list[int] = []

    # ========================================================
    # EPISODES
    # ========================================================

    for episode in range(
        episodes
    ):

        obs, _ = env.reset(
            seed=seed + episode
        )

        done = False
        total_reward = 0.0
        steps = 0

        while not done:

            # Same mask during inference.
            action_masks = (
                env.action_masks()
            )

            action, _ = model.predict(
                obs,
                action_masks=action_masks,
                deterministic=True,
            )

            (
                obs,
                reward,
                terminated,
                truncated,
                info,
            ) = env.step(
                int(action)
            )

            total_reward += float(
                reward
            )

            steps += 1

            action_type = info.get(
                "action_type"
            )

            raw_result = info.get(
                "raw_result",
                {},
            )

            # ----------------------------------------------
            # PIVOT
            # ----------------------------------------------

            if action_type == "pivot":

                pivot_attempts += 1

                if raw_result.get(
                    "ok",
                    False,
                ):
                    successful_pivots += 1

            # ----------------------------------------------
            # EXPLOIT
            # ----------------------------------------------

            elif (
                action_type == "exploit"
                or action_type
                == "crown_jewel_exploit"
            ):

                exploit_attempts += 1

                if raw_result.get(
                    "ok",
                    False,
                ):
                    successful_exploits += 1

            # ----------------------------------------------
            # SCAN
            # ----------------------------------------------

            elif action_type == "scan":

                scan_attempts += 1

                if raw_result.get(
                    "ok",
                    False,
                ):
                    successful_scans += 1

            done = (
                bool(terminated)
                or bool(truncated)
            )

        # ====================================================
        # EPISODE METRICS
        # ====================================================

        rewards.append(
            total_reward
        )

        episode_lengths.append(
            steps
        )

        if total_reward > 0:
            positive_rewards += 1

        if env.env is not None:

            summary = (
                env.env.summary()
            )

            if summary.get(
                "crown_jewel_compromised",
                False,
            ):
                crown_jewel_successes += 1

    # ========================================================
    # AGGREGATION
    # ========================================================

    values = np.asarray(
        rewards,
        dtype=np.float64,
    )

    lengths = np.asarray(
        episode_lengths,
        dtype=np.float64,
    )

    total_steps = max(
        1,
        int(lengths.sum()),
    )

    return {

        "mean_reward":
            float(
                values.mean()
            ),

        "std_reward":
            float(
                values.std()
            ),

        "min_reward":
            float(
                values.min()
            ),

        "max_reward":
            float(
                values.max()
            ),

        "positive_reward_rate":
            float(
                positive_rewards
                / episodes
            ),

        "crown_jewel_rate":
            float(
                crown_jewel_successes
                / episodes
            ),

        "mean_episode_length":
            float(
                lengths.mean()
            ),

        "pivot_success_rate":
            (
                float(
                    successful_pivots
                    / pivot_attempts
                )
                if pivot_attempts
                else 0.0
            ),

        "exploit_success_rate":
            (
                float(
                    successful_exploits
                    / exploit_attempts
                )
                if exploit_attempts
                else 0.0
            ),

        "scan_success_rate":
            (
                float(
                    successful_scans
                    / scan_attempts
                )
                if scan_attempts
                else 0.0
            ),

        "scan_action_rate":
            float(
                scan_attempts
                / total_steps
            ),

        "pivot_action_rate":
            float(
                pivot_attempts
                / total_steps
            ),

        "exploit_action_rate":
            float(
                exploit_attempts
                / total_steps
            ),
    }


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        default=(
            "configs/"
            "twin_topology.yaml"
        ),
    )

    parser.add_argument(
        "--timesteps",
        type=int,
        default=100_000,
    )

    parser.add_argument(
        "--out",
        default="runs/red_ppo.zip",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-4,
    )

    parser.add_argument(
        "--ent-coef",
        type=float,
        default=0.005,
    )

    parser.add_argument(
        "--eval-episodes",
        type=int,
        default=100,
    )

    args = parser.parse_args()

    # ========================================================
    # IMPORT MASKABLE PPO
    # ========================================================

    try:

        from sb3_contrib import (
            MaskablePPO,
        )

        from sb3_contrib.common.wrappers import (
            ActionMasker,
        )

    except ImportError:

        raise ImportError(
            "\n\n"
            "sb3-contrib is required for "
            "action masking.\n\n"
            "Install it with:\n\n"
            "    python -m pip install sb3-contrib\n"
        )

    from stable_baselines3.common.env_checker import (
        check_env,
    )

    # ========================================================
    # LOAD TOPOLOGY
    # ========================================================

    topology = load_topology(
        args.config
    )

    # ========================================================
    # CREATE BASE ENVIRONMENT
    # ========================================================

    base_env = FlatRedGymEnv(
        topology
    )

    # Gymnasium validation.
    check_env(
        base_env,
        warn=True,
    )

    # ========================================================
    # ACTION MASK WRAPPER
    # ========================================================

    env = ActionMasker(
        base_env,
        lambda environment:
            environment.action_masks(),
    )

    # ========================================================
    # MODEL
    # ========================================================

    model = MaskablePPO(

        "MlpPolicy",

        env,

        # ----------------------------------------------------
        # FIXED LEARNING RATE
        # ----------------------------------------------------

        learning_rate=args.learning_rate,

        # ----------------------------------------------------
        # PPO ROLLOUT
        # ----------------------------------------------------

        n_steps=2048,

        batch_size=64,

        n_epochs=10,

        # ----------------------------------------------------
        # DISCOUNT / GAE
        # ----------------------------------------------------

        gamma=0.99,

        gae_lambda=0.95,

        # ----------------------------------------------------
        # PPO CLIPPING
        # ----------------------------------------------------

        clip_range=0.2,

        # ----------------------------------------------------
        # ENTROPY REGULARIZATION
        # ----------------------------------------------------

        ent_coef=args.ent_coef,

        # ----------------------------------------------------
        # VALUE FUNCTION
        # ----------------------------------------------------

        vf_coef=0.5,

        # ----------------------------------------------------
        # GRADIENT CLIPPING
        # ----------------------------------------------------

        max_grad_norm=0.5,

        # ----------------------------------------------------
        # NETWORK
        # ----------------------------------------------------

        policy_kwargs={
            "net_arch": {
                "pi": [128, 128],
                "vf": [128, 128],
            }
        },

        seed=args.seed,

        verbose=1,

        device="cpu",
    )

    # ========================================================
    # CALLBACK
    # ========================================================

    entropy_callback = (
        EntropyMonitorCallback(
            verbose=0
        )
    )

    # ========================================================
    # TRAINING HEADER
    # ========================================================

    print()

    print(
        "========================================"
    )

    print(
        "STARTING MASKABLE PPO TRAINING"
    )

    print(
        "========================================"
    )

    print(
        f"Timesteps:       {args.timesteps}"
    )

    print(
        f"Learning rate:   {args.learning_rate}"
    )

    print(
        f"Entropy coef:    {args.ent_coef}"
    )

    print(
        f"Evaluation:      {args.eval_episodes}"
        " episodes"
    )

    print(
        "Action masking:  ENABLED"
    )

    print(
        "Actions:         EXPLOIT + SCAN + PIVOT"
    )

    print(
        "Entropy score:   POSITIVE 0..1"
    )

    print(
        "Target behavior: entropy gradually declines"
    )

    print()

    # ========================================================
    # TRAIN
    # ========================================================

    model.learn(
        total_timesteps=args.timesteps,
        progress_bar=False,
        callback=entropy_callback,
    )

    # ========================================================
    # SAVE
    # ========================================================

    model.save(
        args.out
    )

    print()

    print(
        f"Saved trained red policy to "
        f"{args.out}"
    )

    # ========================================================
    # EVALUATE
    # ========================================================

    metrics = evaluate_policy(
        model=model,
        env=base_env,
        episodes=args.eval_episodes,
        seed=args.seed + 10_000,
    )

    # ========================================================
    # RESULTS
    # ========================================================

    print()

    print(
        "========================================"
    )

    print(
        "DETERMINISTIC EVALUATION"
    )

    print(
        "========================================"
    )

    print(
        f"Mean reward:          "
        f"{metrics['mean_reward']:.4f}"
    )

    print(
        f"Reward std:           "
        f"{metrics['std_reward']:.4f}"
    )

    print(
        f"Minimum reward:       "
        f"{metrics['min_reward']:.4f}"
    )

    print(
        f"Maximum reward:       "
        f"{metrics['max_reward']:.4f}"
    )

    print(
        f"Positive reward rate: "
        f"{metrics['positive_reward_rate'] * 100:.2f}%"
    )

    print(
        f"Crown jewel rate:     "
        f"{metrics['crown_jewel_rate'] * 100:.2f}%"
    )

    print(
        f"Mean episode length:  "
        f"{metrics['mean_episode_length']:.2f}"
    )

    print(
        f"Pivot success rate:   "
        f"{metrics['pivot_success_rate'] * 100:.2f}%"
    )

    print(
        f"Exploit success rate: "
        f"{metrics['exploit_success_rate'] * 100:.2f}%"
    )

    print(
        f"Scan success rate:    "
        f"{metrics['scan_success_rate'] * 100:.2f}%"
    )

    print(
        f"Scan action rate:     "
        f"{metrics['scan_action_rate'] * 100:.2f}%"
    )

    print(
        f"Pivot action rate:    "
        f"{metrics['pivot_action_rate'] * 100:.2f}%"
    )

    print(
        f"Exploit action rate:  "
        f"{metrics['exploit_action_rate'] * 100:.2f}%"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()