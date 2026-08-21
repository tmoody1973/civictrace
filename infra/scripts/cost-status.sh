#!/usr/bin/env bash
# CivicTrace cost snapshot (per docs/runbooks/cost-security-and-claude-code.md).
# Honest limitation: exact month-to-date spend needs billing export to BigQuery,
# which this project deliberately does not run. This prints the budget config,
# the things that could cost money, and the Console link where spend is read.
set -euo pipefail

PROJECT="${CIVICTRACE_PROJECT:-civictrace-dev-tm}"
REGION="${CIVICTRACE_REGION:-us-central1}"

echo "== CivicTrace cost status · project=${PROJECT} · $(date -u +%Y-%m-%dT%H:%MZ) =="

BILLING_ACCOUNT=$(gcloud billing projects describe "$PROJECT" \
  --format="value(billingAccountName)" | sed 's|billingAccounts/||')
echo "billing account: ${BILLING_ACCOUNT}"

echo "-- budgets --"
gcloud billing budgets list --billing-account="$BILLING_ACCOUNT" \
  --format="table(displayName, amount.specifiedAmount.units, thresholdRules.flatten())" 2>/dev/null \
  || echo "(cannot list budgets with current credentials)"

echo "-- Cloud Run services (cost only when instances > 0) --"
gcloud run services list --project "$PROJECT" --region "$REGION" \
  --format="table(metadata.name, status.url, spec.template.metadata.annotations['autoscaling.knative.dev/maxScale'])" 2>/dev/null \
  || echo "(none)"

echo "-- storage --"
gcloud storage du -s "gs://${PROJECT}-civictrace-vault" "gs://${PROJECT}-civictrace-packets" 2>/dev/null \
  || echo "(buckets not created yet)"

echo "-- model usage (local usage.jsonl files, if any) --"
find "$(git rev-parse --show-toplevel 2>/dev/null || echo .)/backend" -name "usage.jsonl" \
  -exec sh -c 'echo "$1: $(wc -l < "$1") calls"' _ {} \; 2>/dev/null || true

echo "-- cloud model usage (worker model_usage log lines, last 24h) --"
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="civictrace-worker" AND textPayload:"model_usage"' \
  --project "$PROJECT" --freshness 24h --limit 200 --format="value(textPayload)" 2>/dev/null \
  | python3 -c '
import json, sys
rows = [json.loads(line.split("model_usage ", 1)[1]) for line in sys.stdin if "model_usage " in line]
tin = sum(r["input_tokens"] for r in rows); tout = sum(r["output_tokens"] for r in rows)
usd = sum(r["estimated_usd"] for r in rows)
print(f"{len(rows)} model calls · {tin} in / {tout} out tokens · est \${usd:.4f} (list-price estimate; the bill is authoritative)")
' || echo "(no cloud model usage in the last 24h)"

echo "-- exact month-to-date spend --"
echo "https://console.cloud.google.com/billing/${BILLING_ACCOUNT}/reports?project=${PROJECT}"
