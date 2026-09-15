import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from digital_twin.env import TwinEnv
from tests.test_env import make_test_topology
from verification import invariants


def test_no_full_isolation_passes_when_not_all_isolated():
    env = TwinEnv(make_test_topology(), seed=1)
    env.blue_isolate("web")
    result = invariants.check_no_full_isolation(env)
    assert result.passed is True


def test_no_full_isolation_fails_when_all_isolated():
    env = TwinEnv(make_test_topology(), seed=1)
    for node_id in env.topology.nodes:
        env.blue_isolate(node_id)
    result = invariants.check_no_full_isolation(env)
    assert result.passed is False


def test_web_tier_reachable_fails_if_web_isolated():
    env = TwinEnv(make_test_topology(), seed=1)
    env.blue_isolate("web")
    result = invariants.check_web_tier_reachable(env)
    assert result.passed is False


def test_state_invariants_all_pass_on_clean_env():
    env = TwinEnv(make_test_topology(), seed=1)
    results = invariants.check_state(env)
    assert invariants.all_passed(results) is True


if __name__ == "__main__":
    test_no_full_isolation_passes_when_not_all_isolated()
    test_no_full_isolation_fails_when_all_isolated()
    test_web_tier_reachable_fails_if_web_isolated()
    test_state_invariants_all_pass_on_clean_env()
    print("All invariant tests passed.")
