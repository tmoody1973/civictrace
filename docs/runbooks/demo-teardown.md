# Demo Teardown Runbook

## Purpose

Safely reduce or remove disposable CivicTrace demo resources after the video/submission proof has been captured and the project owner confirms that the live environment is no longer needed.

## Preconditions

1. Confirm the recorded demo, deployment screenshots, logs/traces, repository commit, and architecture proof are backed up.
2. Print the exact target GCP project ID, environment, region, and list of resources matching `app=civictrace` and the selected environment label.
3. Confirm no teammate, reviewer, judge, or scheduled task requires the live environment during the teardown window.
4. Obtain explicit human confirmation before any destructive command.

## Procedure

1. Run the implemented `scripts/cost-status.sh` and retain the output with the demo record.
2. Disable Cloud Scheduler source-watch jobs.
3. Inspect Pub/Sub subscriptions and Cloud Tasks queues. Drain, preserve, or intentionally discard work according to the environment policy; do not silently lose a required artifact.
4. Scale Cloud Run services to zero or delete only services defined as disposable in IaC.
5. Remove environment-labeled temporary artifacts and datasets according to Cloud Storage/BigQuery retention policy.
6. Retain only the public replay corpus and evidence required for reproducibility, subject to source terms and project policy.
7. Review active Cloud Run services, Scheduler jobs, queues, buckets, datasets, service accounts, and current billing usage.
8. Record the date, operator, target environment, resources retained, resources deleted, and any outstanding follow-up.

## Safety Rule

Never infer that “the demo is done” means a project may be destroyed. The owner makes that decision. Teardown automation must fail closed if the target environment/project/labels do not exactly match the confirmed plan.

## Automation (MOO-712)

`infra/scripts/teardown-dev.sh` implements steps 2–5 above. **Dry-run is the default** and prints the exact destroy/retain plan. Destruction needs `--destroy` AND typing the exact project id, after the owner's explicit go. It fails closed on any project/label mismatch and never touches `teardown=retain` (the raw-source vault). Verified 2026-08-20: dry-run listed 2 services + queue + topic + BigQuery dataset as destroy targets with labels shown; a wrong project id and a wrong typed confirmation both refused with exit 1 before any change.

## Cost record — Slice 5 (cloud deploy, dev)

| When (UTC) | What | Reading |
|---|---|---|
| 2026-08-20 21:39 | After first cloud replay (MOO-710) | Vault 10.5 MB · packets 0 B · model spend $0 (fixture agents, no Vertex calls) · budget `civictrace-dev-10usd` active (alerts at 50/90/100%) |
| 2026-08-21 01:40 | After studio click-through + cloud approve (MOO-711) | Vault 10.5 MB · packets 6.1 KB (one DRAFT packet) · model spend $0 · both services min 0 / max 2 |
| — | Exact month-to-date dollars | Billing console (script prints the link); read the number there — the CLI cannot |

## Teardown records

_None yet. The dev environment is live for the demo video. Append one row per real `--destroy` run: date, operator, retained, deleted, follow-ups._
