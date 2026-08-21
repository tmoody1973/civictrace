#!/usr/bin/env bash
# CivicTrace dev teardown (MOO-712). DRY-RUN BY DEFAULT: prints the exact plan and exits.
# Real destruction needs --destroy AND typing the exact project id at the prompt, after
# the owner's explicit go per docs/runbooks/demo-teardown.md (demo proof captured first).
# Fails closed on ANY project or label mismatch. Never touches teardown=retain — the
# raw-source vault is the evidence spine and outlives the demo environment.
set -euo pipefail

PROJECT="${CIVICTRACE_PROJECT:-civictrace-dev-tm}"
REGION="${CIVICTRACE_REGION:-us-central1}"
ENVIRONMENT="dev"
TF_DIR="$(cd "$(dirname "$0")/../terraform/environments/dev" && pwd)"
MODE="dry-run"
[ "${1:-}" = "--destroy" ] && MODE="destroy"

refuse() {
  echo "TEARDOWN REFUSED (fail closed): $1"
  exit 1
}

require_labels() { # resource-name labels-string
  local NAME="$1" LABELS="$2" KEY
  for KEY in "app=civictrace" "environment=${ENVIRONMENT}" "teardown=required"; do
    case "$LABELS" in
      *"$KEY"*) ;;
      *) refuse "$NAME is missing label ${KEY} — not provably ours to remove" ;;
    esac
  done
}

echo "== CivicTrace teardown (${MODE}) · project=${PROJECT} env=${ENVIRONMENT} region=${REGION} =="
gcloud projects describe "$PROJECT" --format="value(projectId)" >/dev/null 2>&1 \
  || refuse "project ${PROJECT} not found or not accessible"

# --- Verify every destroy target carries our labels; build the printed plan ------
echo
echo "-- DESTROY targets (label teardown=required, removed via terraform) --"
for SVC in civictrace-api civictrace-worker; do
  LABELS=$(gcloud run services describe "$SVC" --project "$PROJECT" --region "$REGION" \
    --format="value(metadata.labels)" 2>/dev/null) \
    || { echo "   ${SVC}: not deployed (nothing to remove)"; continue; }
  require_labels "$SVC" "$LABELS"
  echo "   Cloud Run service ${SVC}  [${LABELS}]"
done
if gcloud tasks queues describe civictrace-ingest --location "$REGION" --project "$PROJECT" \
  --format="value(name)" >/dev/null 2>&1; then
  # Cloud Tasks queues cannot carry labels; the queue is owned via module.services in IaC.
  echo "   Cloud Tasks queue civictrace-ingest  [terraform module.services]"
fi
TOPIC_LABELS=$(gcloud pubsub topics describe civictrace-source-events --project "$PROJECT" \
  --format="value(labels)" 2>/dev/null || true)
if [ -n "$TOPIC_LABELS" ]; then
  require_labels "topic civictrace-source-events" "$TOPIC_LABELS"
  echo "   Pub/Sub topic civictrace-source-events (+ push subscription)  [${TOPIC_LABELS}]"
fi
BQ_LABELS=$(bq show --format=json --project_id "$PROJECT" civictrace_dev 2>/dev/null \
  | tr -d '{}", ' | tr ':' '=' || true)
if [ -n "$BQ_LABELS" ]; then
  require_labels "BigQuery dataset civictrace_dev" "$BQ_LABELS"
  echo "   BigQuery dataset civictrace_dev (corpus_artifacts — reloads from the manifest in seconds)"
fi

echo
echo "-- RETAINED on purpose (never touched by this script) --"
VAULT="gs://${PROJECT}-civictrace-vault"
VAULT_JSON=$(gcloud storage buckets describe "$VAULT" --format=json 2>/dev/null || true)
case "$VAULT_JSON" in
  *'"teardown": "retain"'*) echo "   ${VAULT}  [teardown=retain — raw-source evidence spine]" ;;
  "") refuse "vault bucket ${VAULT} not found; refusing to proceed blind" ;;
  *) refuse "vault bucket is NOT labeled teardown=retain — labels drifted, investigate first" ;;
esac
echo "   gs://${PROJECT}-civictrace-packets  [objects expire via lifecycle; bucket stays in IaC]"
echo "   Firestore ledger, service accounts, secret shell, image registry  [baseline; separate human decision]"

if [ "$MODE" = "dry-run" ]; then
  echo
  echo "DRY RUN ONLY — nothing was changed. Destructive run: $0 --destroy (owner's go required first)."
  exit 0
fi

# --- Destructive path: typed confirmation, pause deliveries, terraform destroy ---
echo
read -r -p "Type the exact project id to confirm destruction: " TYPED
[ "$TYPED" = "$PROJECT" ] || refuse "typed project id '${TYPED}' does not match ${PROJECT}"

echo "pausing Cloud Tasks queue so nothing is mid-flight during destroy..."
gcloud tasks queues pause civictrace-ingest --location "$REGION" --project "$PROJECT" --quiet || true

echo "destroying services layer (Cloud Run x2, queue, topic, subscription) via terraform..."
terraform -chdir="$TF_DIR" destroy -auto-approve \
  -target='module.services[0]' -var deploy_services=true -var image=unused

echo "destroying BigQuery corpus dataset via terraform..."
terraform -chdir="$TF_DIR" destroy -auto-approve \
  -target='module.baseline.google_bigquery_table.corpus_artifacts' \
  -target='module.baseline.google_bigquery_dataset.corpus'

echo
echo "Teardown complete. Now append the record (date, operator, retained, deleted,"
echo "follow-ups) to docs/runbooks/demo-teardown.md and run infra/scripts/cost-status.sh."
