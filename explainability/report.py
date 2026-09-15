"""
explainability.report
======================

Turns a run directory (produced by orchestrator/arena.py) into the
human-readable report described in docs/ARCHITECTURE.md §7: a
step-by-step causal narrative per episode, the invariant-check results
for every blue action, and a top-line "did red reach the crown jewel"
summary — the shape a security engineer already knows how to read
(closer to an incident timeline than an RL log dump).

Usage:
    python -m explainability.report --run-dir runs/latest
"""
from __future__ import annotations

import argparse
import glob
import json
import os


def render_episode(ep: dict) -> str:
    lines = [f"## Episode (seed={ep['seed']}) — {ep['red_policy']} vs {ep['blue_policy']}\n"]

    lines.append(f"**Outcome:** {'🔴 crown jewel compromised' if ep['crown_jewel_compromised'] else '🔵 held'} "
                  f"in {ep['steps_taken']} steps.\n")
    lines.append(f"**Red reward:** {ep['red_reward']:.2f}  |  **Blue reward:** {ep['blue_reward']:.2f}\n")

    lines.append("### Timeline\n")
    for event in ep["event_log"]:
        actor = event["actor"].upper()
        action = event["action"]
        result = event["result"]
        ok = result.get("ok")
        icon = "✅" if ok else "❌"
        detail_bits = []
        if "detected" in result:
            detail_bits.append("DETECTED by blue" if result["detected"] else "undetected")
        if "severity" in result:
            detail_bits.append(f"severity={result['severity']}")
        if "reason" in result:
            detail_bits.append(result["reason"])
        detail = f" ({', '.join(detail_bits)})" if detail_bits else ""
        lines.append(f"- `step {event['step']:>2}` **{actor}** `{action}` {icon}{detail}")

    lines.append("\n### Blue patch/invariant decisions\n")
    if not ep["blue_reward_events"]:
        lines.append("_No credited blue actions this episode._\n")
    for be in ep["blue_reward_events"]:
        status = "accepted" if be["reward"] >= 0 else "**REJECTED — invariant violation**"
        lines.append(f"- `{be['action']}` → {status}, reward={be['reward']:.2f}")
        for chk in be.get("invariant_checks", []):
            mark = "✔" if chk["passed"] else "✘"
            lines.append(f"    - {mark} `{chk['name']}`: {chk['detail']}")

    lines.append("\n### Reproducibility\n")
    lines.append(
        "Every red-reward event above is backed by the recorded action + "
        "result pair shown in the timeline and is replayable deterministically "
        "given `seed`, per the reproducibility-gated reward rule "
        "(docs/ARCHITECTURE.md §3) — that log entry *is* the proof-of-concept, "
        "not a claim to trust separately.\n"
    )
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default="runs/latest")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    run_dir = args.run_dir
    if os.path.isfile(run_dir):
        # Fallback pointer file written when the platform can't create a
        # symlink (e.g. Windows without admin/Developer Mode) — it just
        # contains the real run directory's path.
        with open(run_dir, encoding="utf-8") as f:
            run_dir = f.read().strip()
    args.run_dir = run_dir

    ep_files = sorted(glob.glob(os.path.join(args.run_dir, "episode_*.json")))
    summary_path = os.path.join(args.run_dir, "run_summary.json")

    sections = ["# SPCIS Episode Report\n"]
    if os.path.exists(summary_path):
        with open(summary_path, encoding="utf-8") as f:
            run_summary = json.load(f)
        sections.append(
            f"Run of {run_summary['n_episodes']} episodes — "
            f"crown-jewel compromise rate: {run_summary['crown_jewel_compromise_rate']:.0%}, "
            f"avg red reward: {run_summary['avg_red_reward']:.2f}, "
            f"avg blue reward: {run_summary['avg_blue_reward']:.2f}.\n"
        )

    for path in ep_files:
        with open(path, encoding="utf-8") as f:
            ep = json.load(f)
        sections.append(render_episode(ep))

    report = "\n\n---\n\n".join(sections)
    out_path = args.out or os.path.join(args.run_dir, "report.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report written to {out_path}")


if __name__ == "__main__":
    main()
