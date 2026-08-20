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

echo "-- exact month-to-date spend --"
echo "https://console.cloud.google.com/billing/${BILLING_ACCOUNT}/reports?project=${PROJECT}"
