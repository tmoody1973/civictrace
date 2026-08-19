# CivicTrace Operational Scripts

These scripts are deliberately listed but not implemented in the documentation pack. Implement them only after the chosen infrastructure-as-code configuration and environment labels exist.

| Planned script | Purpose | Safety requirement |
|---|---|---|
| `verify-cloud-guardrails.sh` | Validate Cloud Run minimum/maximum instances, worker IAM, bucket lifecycle, labels, required budgets/alerts, and absence of tracked secrets. | Read-only; exits nonzero on a policy violation. |
| `deploy-demo.sh` | Execute reviewed IaC apply and deploy the current application revision to the confirmed demo environment. | Must print target project/environment/region and require explicit confirmation before any apply/deploy. |
| `cost-status.sh` | Summarize environment-labeled resources, configured caps, queue state, and available billing/usage signals. | Read-only; must not claim that budgets are hard caps. |
| `demo-teardown.sh` | Disable schedules, scale/delete disposable environment-labeled services, clean temporary artifacts, and report retained resources. | Must fail closed without exact target labels and explicit human confirmation. |
| `replay-corpus.sh` | Submit the reviewed demo corpus to source/event pipeline for deterministic demo replay. | Must use only `docs/sources/corpus-manifest.yaml` fixtures and never hit unapproved source domains. |

Do not put service-account JSON or API keys in a script. Read configuration from the environment/Secret Manager and ensure destructive actions use the runbook approval process.
