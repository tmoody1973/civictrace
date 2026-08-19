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
