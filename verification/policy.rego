# verification/policy.rego
#
# Reference illustration of what the invariant checks in invariants.py
# look like as OPA/Rego policy-as-code, per docs/ARCHITECTURE.md §4.
# Not wired into the toy loop (invariants.py is the enforced version) —
# this is here to show the real-deployment shape, where a blue-proposed
# infra diff would be evaluated with `opa eval` against rules like these
# before being counted as a valid patch candidate.

package spcis.blue_patch

import future.keywords.in

# Deny if a proposed patch isolates every node in the topology.
deny[msg] {
    count(input.isolated_nodes) >= count(input.all_nodes)
    msg := "patch would isolate 100% of nodes — outage, not a fix"
}

# Deny if a proposed patch isolates a node in the required-reachable set
# (e.g. public web/api tier) that legitimate traffic depends on.
deny[msg] {
    some node in input.isolated_nodes
    node in input.required_reachable_nodes
    msg := sprintf("patch isolates required-reachable node %v", [node])
}

# Deny if a proposed IAM change grants a wildcard action+resource.
deny[msg] {
    some stmt in input.iam_statement_diff
    stmt.effect == "Allow"
    stmt.action == "*"
    stmt.resource == "*"
    msg := "patch grants *:* IAM permission"
}

# A patch is allowed only if there are no deny reasons.
allow {
    count(deny) == 0
}
