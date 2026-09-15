"""
SPCIS Streamlit Showcase
========================

Interactive cybersecurity digital twin demonstrating:

    Red AI Agent
        EXPLOIT
        SCAN
        PIVOT

    Blue AI Defender
        DETECTION
        RESPONSE
        ISOLATION / PATCHING

    PPO Analytics
        Reward
        Entropy
        Action distribution
        Crown-jewel compromise

Run:

    python -m streamlit run streamlit_app.py
"""

from __future__ import annotations

import math
import os
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import torch
import yaml

from digital_twin.env import Topology
from red_agent.train import FlatRedGymEnv
from sb3_contrib import MaskablePPO


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SPCIS Cyber Digital Twin",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #0b1020;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    .hero {
        padding: 1.5rem 2rem;
        border-radius: 18px;
        background:
            linear-gradient(
                135deg,
                #111827 0%,
                #172554 50%,
                #0f172a 100%
            );
        border: 1px solid #334155;
        margin-bottom: 1rem;
    }

    .hero h1 {
        margin-bottom: 0.25rem;
        font-size: 2.4rem;
    }

    .hero p {
        color: #94a3b8;
        font-size: 1.05rem;
    }

    .status-card {
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 1rem;
        background: #111827;
    }

    .small-label {
        color: #94a3b8;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .big-number {
        font-size: 1.8rem;
        font-weight: 700;
    }

    .red-text {
        color: #ef4444;
    }

    .blue-text {
        color: #38bdf8;
    }

    .green-text {
        color: #22c55e;
    }

    .orange-text {
        color: #f59e0b;
    }

    .event-row {
        padding: 0.7rem 0;
        border-bottom: 1px solid #1e293b;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PATHS
# ============================================================

CONFIG_PATH = os.path.join(
    "configs",
    "twin_topology.yaml",
)

MODEL_PATH = os.path.join(
    "runs",
    "red_ppo.zip",
)


# ============================================================
# SESSION STATE
# ============================================================

def initialize_state() -> None:

    defaults = {
        "simulation_started": False,
        "env": None,
        "observation": None,

        "episode_reward": 0.0,
        "episode_step": 0,
        "episode_done": False,

        "events": [],
        "reward_history": [],
        "entropy_history": [],
        "action_history": [],

        "red_successes": 0,
        "red_attempts": 0,

        "pivot_successes": 0,
        "pivot_attempts": 0,

        "scan_successes": 0,
        "scan_attempts": 0,

        "exploit_successes": 0,
        "exploit_attempts": 0,

        "crown_jewel": False,

        "last_action": "None",
        "last_reward": 0.0,

        "model": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


initialize_state()


# ============================================================
# LOAD TOPOLOGY
# ============================================================

@st.cache_resource
def load_topology() -> Topology:

    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        data = yaml.safe_load(file)

    return Topology.from_dict(data)


# ============================================================
# LOAD MODEL
# ============================================================

@st.cache_resource
def load_model():

    if not os.path.exists(
        MODEL_PATH
    ):
        return None

    try:

        model = MaskablePPO.load(
            MODEL_PATH,
            device="cpu",
        )

        return model

    except Exception:

        return None


# ============================================================
# CREATE ENVIRONMENT
# ============================================================

def create_environment() -> FlatRedGymEnv:

    topology = load_topology()

    return FlatRedGymEnv(
        topology,
        max_vulns_per_node=4,
        max_steps=40,
    )


# ============================================================
# MODEL ENTROPY
# ============================================================

def calculate_entropy_score(
    model,
    observation,
) -> float:
    """
    Return positive normalized entropy in [0, 1].

    0.0 = nearly deterministic
    1.0 = maximum entropy
    """

    if model is None:
        return 0.0

    try:

        observation_array = np.asarray(
            observation,
            dtype=np.float32,
        )

        obs_tensor, _ = (
            model.policy.obs_to_tensor(
                observation_array
            )
        )

        with torch.no_grad():

            distribution = (
                model.policy.get_distribution(
                    obs_tensor
                )
            )

            entropy = (
                distribution
                .distribution
                .entropy()
            )

            actual_entropy = float(
                entropy.mean()
                .cpu()
                .item()
            )

        n_actions = int(
            model.action_space.n
        )

        max_entropy = math.log(
            max(
                2,
                n_actions,
            )
        )

        normalized_entropy = (
            actual_entropy
            / max_entropy
            if max_entropy > 0
            else 0.0
        )

        return float(
            np.clip(
                normalized_entropy,
                0.0,
                1.0,
            )
        )

    except Exception:

        return 0.0


# ============================================================
# RESET SIMULATION
# ============================================================

def reset_simulation() -> None:

    env = create_environment()

    observation, _ = env.reset(
        seed=int(
            np.random.randint(
                0,
                1_000_000,
            )
        )
    )

    st.session_state.env = env
    st.session_state.observation = observation

    st.session_state.simulation_started = True

    st.session_state.episode_reward = 0.0
    st.session_state.episode_step = 0
    st.session_state.episode_done = False

    st.session_state.events = []
    st.session_state.reward_history = []
    st.session_state.entropy_history = []
    st.session_state.action_history = []

    st.session_state.red_successes = 0
    st.session_state.red_attempts = 0

    st.session_state.pivot_successes = 0
    st.session_state.pivot_attempts = 0

    st.session_state.scan_successes = 0
    st.session_state.scan_attempts = 0

    st.session_state.exploit_successes = 0
    st.session_state.exploit_attempts = 0

    st.session_state.crown_jewel = False

    st.session_state.last_action = "None"
    st.session_state.last_reward = 0.0


# ============================================================
# DESCRIBE ACTION
# ============================================================

def describe_action(
    action_index: int,
    env: FlatRedGymEnv,
) -> str:

    action = env.actions[
        action_index
    ]

    action_name = type(
        action
    ).__name__

    if action_name == "ExploitAction":

        return (
            f"EXPLOIT → "
            f"{action.node_id} "
            f"(vulnerability slot "
            f"{action.vuln_slot})"
        )

    if action_name == "ScanAction":

        return (
            f"SCAN → "
            f"{action.node_id}"
        )

    if action_name == "PivotAction":

        return (
            f"PIVOT → "
            f"{action.source_id} "
            f"→ "
            f"{action.target_id}"
        )

    return "UNKNOWN"


# ============================================================
# EXECUTE ONE AI STEP
# ============================================================

def execute_step() -> None:

    env = st.session_state.env
    model = st.session_state.model

    if env is None:
        return

    if st.session_state.episode_done:
        return

    observation = (
        st.session_state.observation
    )

    # --------------------------------------------------------
    # MODEL ACTION
    # --------------------------------------------------------

    if model is not None:

        action_masks = (
            env.action_masks()
        )

        action, _ = model.predict(
            observation,
            action_masks=action_masks,
            deterministic=True,
        )

        action = int(action)

    else:

        mask = env.action_masks()

        valid_actions = (
            np.flatnonzero(mask)
        )

        if len(valid_actions) == 0:
            return

        action = int(
            np.random.choice(
                valid_actions
            )
        )

    action_description = (
        describe_action(
            action,
            env,
        )
    )

    # --------------------------------------------------------
    # STEP ENVIRONMENT
    # --------------------------------------------------------

    (
        new_observation,
        reward,
        terminated,
        truncated,
        info,
    ) = env.step(
        action
    )

    st.session_state.observation = (
        new_observation
    )

    st.session_state.episode_reward += (
        float(reward)
    )

    st.session_state.episode_step += 1

    st.session_state.last_reward = (
        float(reward)
    )

    st.session_state.last_action = (
        action_description
    )

    # --------------------------------------------------------
    # ENTROPY
    # --------------------------------------------------------

    entropy_score = calculate_entropy_score(
        model,
        new_observation,
    )

    st.session_state.entropy_history.append(
        entropy_score
    )

    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    st.session_state.action_history.append(
        action_description
    )

    st.session_state.reward_history.append(
        float(reward)
    )

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    action_type = info.get(
        "action_type",
        "unknown",
    )

    raw_result = info.get(
        "raw_result",
        {},
    )

    ok = bool(
        raw_result.get(
            "ok",
            False,
        )
    )

    if action_type in {
        "exploit",
        "crown_jewel_exploit",
    }:

        st.session_state.exploit_attempts += 1

        if ok:

            st.session_state.exploit_successes += 1

    elif action_type == "pivot":

        st.session_state.pivot_attempts += 1

        if ok:

            st.session_state.pivot_successes += 1

    elif action_type == "scan":

        st.session_state.scan_attempts += 1

        if ok:

            st.session_state.scan_successes += 1

    # --------------------------------------------------------
    # CROWN JEWEL
    # --------------------------------------------------------

    if info.get(
        "crown_jewel_compromised",
        False,
    ):

        st.session_state.crown_jewel = True

    # --------------------------------------------------------
    # EVENT LOG
    # --------------------------------------------------------

    event = {
        "step":
            st.session_state.episode_step,

        "action":
            action_description,

        "reward":
            float(reward),

        "result":
            "SUCCESS"
            if ok
            else "FAILED",
    }

    st.session_state.events.insert(
        0,
        event,
    )

    st.session_state.events = (
        st.session_state.events[:30]
    )

    # --------------------------------------------------------
    # DONE
    # --------------------------------------------------------

    st.session_state.episode_done = (
        bool(terminated)
        or bool(truncated)
    )


# ============================================================
# TOPOLOGY GRAPH
# ============================================================

def render_topology() -> None:

    env = st.session_state.env

    if env is None:

        st.info(
            "Start a simulation to visualize "
            "the digital twin."
        )

        return

    graph = nx.DiGraph()

    # --------------------------------------------------------
    # NODES
    # --------------------------------------------------------

    for node_id in env.node_ids:

        node = (
            env.env.topology.nodes[
                node_id
            ]
        )

        compromised = bool(
            node.compromised
        )

        known = (
            node_id
            in env.env.red_known_nodes
        )

        isolated = (
            node_id
            in env.env.isolated_nodes
        )

        if isolated:

            status = "ISOLATED"

        elif compromised:

            status = "COMPROMISED"

        elif known:

            status = "DISCOVERED"

        else:

            status = "UNKNOWN"

        graph.add_node(
            node_id,
            status=status,
        )

    # --------------------------------------------------------
    # EDGES
    # --------------------------------------------------------

    for target_id in env.node_ids:

        target_node = (
            env.env.topology.nodes[
                target_id
            ]
        )

        reachable_from = getattr(
            target_node,
            "reachable_from",
            [],
        )

        for source_id in reachable_from:

            if source_id in env.node_ids:

                graph.add_edge(
                    source_id,
                    target_id,
                )

    # --------------------------------------------------------
    # LAYOUT
    # --------------------------------------------------------

    try:

        positions = nx.spring_layout(
            graph,
            seed=7,
            k=1.8,
        )

    except Exception:

        positions = nx.circular_layout(
            graph
        )

    # --------------------------------------------------------
    # EDGES
    # --------------------------------------------------------

    edge_x = []
    edge_y = []

    for source, target in graph.edges:

        x0, y0 = positions[
            source
        ]

        x1, y1 = positions[
            target
        ]

        edge_x.extend(
            [
                x0,
                x1,
                None,
            ]
        )

        edge_y.extend(
            [
                y0,
                y1,
                None,
            ]
        )

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(
            width=1.5,
            color="#64748b",
        ),
        hoverinfo="none",
    )

    # --------------------------------------------------------
    # NODES
    # --------------------------------------------------------

    node_x = []
    node_y = []

    labels = []
    hover_text = []
    colors = []

    for node_id in graph.nodes:

        x, y = positions[
            node_id
        ]

        node_x.append(x)
        node_y.append(y)

        status = graph.nodes[
            node_id
        ]["status"]

        labels.append(
            node_id
        )

        hover_text.append(
            f"<b>{node_id}</b><br>"
            f"Status: {status}"
        )

        if status == "COMPROMISED":

            colors.append(
                "#ef4444"
            )

        elif status == "ISOLATED":

            colors.append(
                "#f59e0b"
            )

        elif status == "DISCOVERED":

            colors.append(
                "#38bdf8"
            )

        else:

            colors.append(
                "#64748b"
            )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=labels,
        textposition="bottom center",
        hovertext=hover_text,
        hoverinfo="text",
        marker=dict(
            size=28,
            color=colors,
            line=dict(
                width=2,
                color="#e2e8f0",
            ),
        ),
    )

    # --------------------------------------------------------
    # FIGURE
    # --------------------------------------------------------

    fig = go.Figure(
        data=[
            edge_trace,
            node_trace,
        ]
    )

    fig.update_layout(
        height=580,
        paper_bgcolor="#0b1020",
        plot_bgcolor="#0b1020",
        showlegend=False,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
        xaxis=dict(
            visible=False
        ),
        yaxis=dict(
            visible=False
        ),
    )

    st.plotly_chart(
        fig,
        width="stretch",
        key="digital_twin_topology",
    )


# ============================================================
# KPI CARDS
# ============================================================

def render_kpis() -> None:

    reward = (
        st.session_state.episode_reward
    )

    entropy = (
        st.session_state.entropy_history[-1]
        if st.session_state.entropy_history
        else 0.0
    )

    crown = (
        "COMPROMISED"
        if st.session_state.crown_jewel
        else "SECURE"
    )

    crown_color = (
        "red-text"
        if st.session_state.crown_jewel
        else "green-text"
    )

    cols = st.columns(
        6
    )

    cards = [
        (
            "EPISODE REWARD",
            f"{reward:.2f}",
            "orange-text",
        ),

        (
            "ENTROPY SCORE",
            f"{entropy:.3f}",
            "blue-text",
        ),

        (
            "CROWN JEWEL",
            crown,
            crown_color,
        ),

        (
            "PIVOTS",
            str(
                st.session_state.pivot_attempts
            ),
            "red-text",
        ),

        (
            "EXPLOITS",
            str(
                st.session_state.exploit_attempts
            ),
            "red-text",
        ),

        (
            "STEPS",
            str(
                st.session_state.episode_step
            ),
            "blue-text",
        ),
    ]

    for column, card in zip(
        cols,
        cards,
    ):

        label, value, color = card

        with column:

            st.markdown(
                f"""
                <div class="status-card">
                    <div class="small-label">
                        {label}
                    </div>
                    <div class="big-number {color}">
                        {value}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# REWARD CHART
# ============================================================

def render_reward_chart(
    key: str,
) -> None:

    rewards = (
        st.session_state.reward_history
    )

    if not rewards:

        st.info(
            "Reward history will appear "
            "after the first action."
        )

        return

    cumulative = np.cumsum(
        rewards
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            y=rewards,
            mode="lines+markers",
            name="Step Reward",
        )
    )

    fig.add_trace(
        go.Scatter(
            y=cumulative,
            mode="lines",
            name="Cumulative Reward",
        )
    )

    fig.update_layout(
        title="Red Agent Reward",
        height=320,
        paper_bgcolor="#0b1020",
        plot_bgcolor="#0b1020",
        font=dict(
            color="#e2e8f0"
        ),
        margin=dict(
            l=20,
            r=20,
            t=50,
            b=20,
        ),
    )

    st.plotly_chart(
        fig,
        width="stretch",
        key=key,
    )


# ============================================================
# ENTROPY CHART
# ============================================================

def render_entropy_chart() -> None:

    values = (
        st.session_state.entropy_history
    )

    if not values:

        st.info(
            "Entropy will appear after "
            "the first AI action."
        )

        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            y=values,
            mode="lines+markers",
            name="Entropy Score",
        )
    )

    fig.add_hline(
        y=0.2,
        line_dash="dash",
        annotation_text="Low exploration",
    )

    fig.update_yaxes(
        range=[0, 1]
    )

    fig.update_layout(
        title="Normalized Policy Entropy",
        height=320,
        paper_bgcolor="#0b1020",
        plot_bgcolor="#0b1020",
        font=dict(
            color="#e2e8f0"
        ),
        margin=dict(
            l=20,
            r=20,
            t=50,
            b=20,
        ),
    )

    st.plotly_chart(
        fig,
        width="stretch",
        key="entropy_chart",
    )


# ============================================================
# EVENT LOG
# ============================================================

def render_event_log() -> None:

    if not st.session_state.events:

        st.info(
            "No actions executed yet."
        )

        return

    dataframe = pd.DataFrame(
        st.session_state.events
    )

    st.dataframe(
        dataframe,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# MODEL INFORMATION
# ============================================================

def render_model_info() -> None:

    model = st.session_state.model

    if model is None:

        st.warning(
            """
            `runs/red_ppo.zip` was not found.

            The dashboard will still work in fallback
            simulation mode, but it will not demonstrate
            the trained PPO agent.
            """
        )

        return

    col1, col2, col3, col4 = st.columns(
        4
    )

    with col1:

        st.metric(
            "MODEL",
            "Maskable PPO",
        )

    with col2:

        st.metric(
            "POLICY",
            "MlpPolicy",
        )

    with col3:

        st.metric(
            "DEVICE",
            "CPU",
        )

    with col4:

        st.metric(
            "ACTION SPACE",
            str(
                model.action_space.n
            ),
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🛡️ SPCIS"
    )

    st.caption(
        "Cybersecurity Digital Twin"
    )

    st.divider()

    st.markdown(
        "### Simulation Controls"
    )

    if st.button(
        "🚀 Start / Reset Simulation",
        width="stretch",
        key="start_reset_button",
    ):

        reset_simulation()

        st.rerun()

    if st.button(
        "⚡ Execute AI Step",
        width="stretch",
        key="execute_ai_step_button",
        disabled=(
            not st.session_state.simulation_started
            or st.session_state.episode_done
        ),
    ):

        execute_step()

        st.rerun()

    auto_steps = st.slider(
        "Auto-run steps",
        min_value=1,
        max_value=20,
        value=5,
        key="auto_steps_slider",
    )

    if st.button(
        "▶ Run AI Automatically",
        width="stretch",
        key="run_ai_auto_button",
        disabled=(
            not st.session_state.simulation_started
            or st.session_state.episode_done
        ),
    ):

        for _ in range(
            auto_steps
        ):

            if st.session_state.episode_done:
                break

            execute_step()

        st.rerun()

    st.divider()

    st.markdown(
        "### Model"
    )

    if os.path.exists(
        MODEL_PATH
    ):

        st.success(
            "red_ppo.zip detected"
        )

    else:

        st.error(
            "red_ppo.zip not found"
        )

    st.divider()

    st.caption(
        "SPCIS • Autonomous Red/Blue "
        "Cyber Defense Research"
    )


# ============================================================
# LOAD MODEL INTO SESSION
# ============================================================

if st.session_state.model is None:

    st.session_state.model = (
        load_model()
    )


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">

        <h1>🛡️ SPCIS Cyber Digital Twin</h1>

        <p>
        Autonomous Red-vs-Blue cybersecurity environment
        powered by reinforcement learning, topology-aware
        reasoning, action masking, and dynamic defense.
        </p>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# MODEL STATUS
# ============================================================

render_model_info()

st.write("")


# ============================================================
# KPI
# ============================================================

render_kpis()

st.write("")


# ============================================================
# MAIN TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🌐 Digital Twin",
        "⚔️ Red vs Blue",
        "📈 RL Analytics",
        "📋 Event Timeline",
    ]
)


# ============================================================
# TAB 1 — DIGITAL TWIN
# ============================================================

with tab1:

    st.subheader(
        "Live Digital Twin Topology"
    )

    if not st.session_state.simulation_started:

        st.info(
            "Click **Start / Reset Simulation** "
            "in the sidebar."
        )

    render_topology()

    st.caption(
        """
        Node colors:

        🔴 compromised

        🔵 discovered

        🟠 isolated

        ⚪ unknown
        """
    )


# ============================================================
# TAB 2 — RED VS BLUE
# ============================================================

with tab2:

    left, right = st.columns(
        2
    )

    # --------------------------------------------------------
    # RED
    # --------------------------------------------------------

    with left:

        st.subheader(
            "🔴 Red AI Agent"
        )

        exploit_rate = (
            st.session_state.exploit_successes
            / max(
                1,
                st.session_state.exploit_attempts,
            )
        )

        pivot_rate = (
            st.session_state.pivot_successes
            / max(
                1,
                st.session_state.pivot_attempts,
            )
        )

        scan_rate = (
            st.session_state.scan_successes
            / max(
                1,
                st.session_state.scan_attempts,
            )
        )

        st.metric(
            "Exploit Success",
            f"{exploit_rate * 100:.1f}%",
        )

        st.metric(
            "Pivot Success",
            f"{pivot_rate * 100:.1f}%",
        )

        st.metric(
            "Scan Success",
            f"{scan_rate * 100:.1f}%",
        )

        st.markdown(
            f"""
            **Last AI action**

            `{st.session_state.last_action}`
            """
        )

        st.metric(
            "Last Reward",
            f"{st.session_state.last_reward:+.3f}",
        )

    # --------------------------------------------------------
    # BLUE
    # --------------------------------------------------------

    with right:

        st.subheader(
            "🔵 Blue AI Defender"
        )

        st.markdown(
            """
            The blue policy continuously reacts to
            red-agent behavior.

            Typical defensive responses include:

            • threat detection

            • node isolation

            • vulnerability patching

            • security-state changes

            This creates the actual adversarial
            red-vs-blue environment rather than
            a static ML demo.
            """
        )

    st.divider()

    render_reward_chart(
        key="reward_chart_red_blue",
    )


# ============================================================
# TAB 3 — RL ANALYTICS
# ============================================================

with tab3:

    st.subheader(
        "Reinforcement Learning Analytics"
    )

    col1, col2 = st.columns(
        2
    )

    # --------------------------------------------------------
    # REWARD
    # --------------------------------------------------------

    with col1:

        st.markdown(
            "### 🎯 Reward"
        )

        st.metric(
            "Episode Reward",
            f"{st.session_state.episode_reward:.2f}",
        )

        render_reward_chart(
            key="reward_chart_rl_analytics",
        )

    # --------------------------------------------------------
    # ENTROPY
    # --------------------------------------------------------

    with col2:

        st.markdown(
            "### 🧠 Entropy"
        )

        entropy = (
            st.session_state.entropy_history[-1]
            if st.session_state.entropy_history
            else 0.0
        )

        st.metric(
            "Entropy Score",
            f"{entropy:.3f}",
        )

        st.progress(
            float(
                np.clip(
                    entropy,
                    0.0,
                    1.0,
                )
            )
        )

        st.caption(
            """
            0.0 = nearly deterministic

            1.0 = maximum exploration
            """
        )

        render_entropy_chart()

    st.divider()

    # --------------------------------------------------------
    # LEARNING METRICS
    # --------------------------------------------------------

    st.subheader(
        "What the model is learning"
    )

    exploit_rate = (
        st.session_state.exploit_successes
        / max(
            1,
            st.session_state.exploit_attempts,
        )
    )

    pivot_rate = (
        st.session_state.pivot_successes
        / max(
            1,
            st.session_state.pivot_attempts,
        )
    )

    scan_rate = (
        st.session_state.scan_successes
        / max(
            1,
            st.session_state.scan_attempts,
        )
    )

    metrics_df = pd.DataFrame(
        {
            "Metric": [
                "Episode Reward",
                "Entropy Score",
                "Exploit Success Rate",
                "Pivot Success Rate",
                "Scan Success Rate",
                "Crown Jewel",
            ],

            "Value": [
                float(
                    st.session_state.episode_reward
                ),

                float(
                    entropy
                ),

                float(
                    exploit_rate
                ),

                float(
                    pivot_rate
                ),

                float(
                    scan_rate
                ),

                int(
                    st.session_state.crown_jewel
                ),
            ],
        }
    )

    st.dataframe(
        metrics_df,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# TAB 4 — EVENT TIMELINE
# ============================================================

with tab4:

    st.subheader(
        "Attack / Defense Event Timeline"
    )

    render_event_log()

    if st.session_state.crown_jewel:

        st.error(
            "🚨 CROWN JEWEL COMPROMISED"
        )

    elif st.session_state.episode_done:

        st.success(
            "Episode completed without "
            "crown-jewel compromise."
        )

    else:

        st.info(
            "Simulation running."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    """
    SPCIS — Autonomous Cybersecurity Digital Twin |
    Maskable PPO + Red/Blue Agents + Topology-Aware RL
    """
)