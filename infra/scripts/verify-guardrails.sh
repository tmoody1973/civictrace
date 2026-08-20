#!/usr/bin/env bash
# CivicTrace guardrail check (run before every deploy, per .claude/rules/gcp-operations.md).
# Fails non-zero on: a Cloud Run service with min>0 or no finite max, an unauthenticated
# worker, a public bucket, a missing budget, or a target resource missing the app label.
set -euo pipefail

PROJECT="${CIVICTRACE_PROJECT:-civictrace-dev-tm}"
REGION="${CIVICTRACE_REGION:-us-central1}"
FAILURES=0

fail() {
  echo "GUARDRAIL FAIL: $1"
  FAILURES=$((FAILURES + 1))
}

pass() {
  echo "ok: $1"
}

echo "== CivicTrace guardrails · project=${PROJECT} region=${REGION} =="

# --- Cloud Run: min 0, finite max, worker never public ---------------------------
SERVICES=$(gcloud run services list --project "$PROJECT" --region "$REGION" \
  --format="value(metadata.name)" 2>/dev/null || true)
if [ -z "$SERVICES" ]; then
  pass "no Cloud Run services deployed yet"
else
  for SVC in $SERVICES; do
    MIN=$(gcloud run services describe "$SVC" --project "$PROJECT" --region "$REGION" \
      --format="value(spec.template.metadata.annotations['autoscaling.knative.dev/minScale'])")
    MAX=$(gcloud run services describe "$SVC" --project "$PROJECT" --region "$REGION" \
      --format="value(spec.template.metadata.annotations['autoscaling.knative.dev/maxScale'])")
    [ "${MIN:-0}" = "0" ] || [ -z "${MIN:-}" ] || fail "$SVC has min instances ${MIN} (must be 0)"
    [ -n "${MAX:-}" ] && [ "${MAX:-0}" -le 4 ] || fail "$SVC has no finite max instances (<=4 required)"
    pass "$SVC min=${MIN:-0} max=${MAX:-unset}"
    if [ "$SVC" = "civictrace-worker" ]; then
      PUBLIC=$(gcloud run services get-iam-policy "$SVC" --project "$PROJECT" --region "$REGION" \
        --format=json | grep -c allUsers || true)
      [ "$PUBLIC" = "0" ] && pass "worker is not publicly invocable" \
        || fail "civictrace-worker allows allUsers invocation"
    fi
  done
fi

# --- Buckets: never public, labeled --------------------------------------------
for BUCKET in "${PROJECT}-civictrace-vault" "${PROJECT}-civictrace-packets"; do
  if gcloud storage buckets describe "gs://$BUCKET" --format=json >/tmp/bucket.json 2>/dev/null; then
    grep -q '"publicAccessPrevention": "enforced"' /tmp/bucket.json \
      && pass "$BUCKET public access prevention enforced" \
      || fail "$BUCKET does not enforce public access prevention"
    grep -q '"app": "civictrace"' /tmp/bucket.json \
      && pass "$BUCKET labeled app=civictrace" \
      || fail "$BUCKET missing app=civictrace label"
  else
    echo "note: bucket $BUCKET not created yet"
  fi
done

# --- Budget exists (created manually in MOO-690; documented IaC exception) -------
BILLING_ACCOUNT=$(gcloud billing projects describe "$PROJECT" \
  --format="value(billingAccountName)" 2>/dev/null | sed 's|billingAccounts/||')
if [ -n "$BILLING_ACCOUNT" ]; then
  BUDGETS=$(gcloud billing budgets list --billing-account="$BILLING_ACCOUNT" \
    --format="value(displayName)" 2>/dev/null | grep -c civictrace || true)
  [ "$BUDGETS" -ge 1 ] && pass "civictrace budget exists on billing account" \
    || fail "no civictrace budget on billing account $BILLING_ACCOUNT"
else
  fail "project has no billing account attached"
fi

# --- No Owner/Editor grants to app service accounts ------------------------------
BROAD=$(gcloud projects get-iam-policy "$PROJECT" --format=json \
  | python3 -c "
import json, sys
policy = json.load(sys.stdin)
offenders = [
    member
    for binding in policy.get('bindings', [])
    if binding['role'] in ('roles/owner', 'roles/editor')
    for member in binding.get('members', [])
    if 'civictrace' in member
]
print(' '.join(offenders))
")
[ -z "$BROAD" ] && pass "no civictrace service account holds Owner/Editor" \
  || fail "broad role on: $BROAD"

echo "== ${FAILURES} failure(s) =="
exit "$([ "$FAILURES" -eq 0 ] && echo 0 || echo 1)"
