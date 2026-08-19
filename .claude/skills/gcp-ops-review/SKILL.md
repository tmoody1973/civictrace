---
name: gcp-ops-review
description: Review CivicTrace Google Cloud changes for cost, security, lifecycle, source-policy, and demo-readiness guardrails.
---

# CivicTrace GCP Operations Review

Use this skill before deploying, changing infrastructure, enabling a new source adapter, starting a backfill, exposing an endpoint, recording the hackathon demo, or tearing down demo resources.

## Required Reading

Read `CLAUDE.md`, `.claude/rules/gcp-operations.md`, `.claude/rules/privacy-and-evidence.md`, the affected `infra/` files, the relevant source allowlist, and the applicable runbook.

## Review Procedure

1. Summarize the proposed resource changes, identity changes, endpoint exposure, source domains, model calls, expected artifact volume, and retention behavior.
2. Check scale-to-zero, finite instance caps, minimal CPU/memory, queue concurrency/retry limits, model selection, source adapter allowlist, Storage lifecycle, Firestore/BigQuery purpose, endpoint authentication, IAM least privilege, secret handling, and resource labels.
3. Verify whether the change alters the evidence/provenance, MPS privacy, or human-approval boundary.
4. Classify each finding as `BLOCKER`, `REQUIRED_FIX`, or `RECOMMENDATION`.
5. Do not deploy, modify billing, expose endpoints, or execute teardown. Present a plan and wait for explicit human approval.

## Required Output

Return a Markdown table with: Control, Current State, Risk, Required Change, Verification Command/Test, and Owner. End with an explicit go/no-go decision and a list of human approvals required.

## Stop Conditions

Stop and request human direction if the change would expose a public endpoint, add automated external communication, expand MPS data scope, remove an approval gate, increase a service cap, use a premium model by default, introduce always-on infrastructure, or delete resources.
