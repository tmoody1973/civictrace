# Local Vertex AI setup (MOO-690)

**Who runs this:** Tarik, in his own Google account. Claude does not run `gcloud` for you.
**What you get:** one dev project, Vertex AI turned on, your laptop signed in, a $10 budget alert.
**What this does NOT create:** no service accounts, no key files, no Cloud Run, no buckets. Those are Slice 5.

Pick a project id once and reuse it everywhere below (lowercase, unique, e.g. `civictrace-dev-tm`).

```bash
export GOOGLE_CLOUD_PROJECT=civictrace-dev-tm      # change the suffix if taken
export GOOGLE_CLOUD_LOCATION=us-central1
```

## 1. Sign in and make the project

```bash
gcloud auth login
gcloud projects create "$GOOGLE_CLOUD_PROJECT" --name="CivicTrace Dev" --labels=app=civictrace,environment=dev,teardown=required
gcloud config set project "$GOOGLE_CLOUD_PROJECT"
```

## 2. Link a billing account (needs a card on the account)

```bash
gcloud billing accounts list                         # copy the ACCOUNT_ID (format 0X0X0X-0X0X0X-0X0X0X)
gcloud billing projects link "$GOOGLE_CLOUD_PROJECT" --billing-account=ACCOUNT_ID
```

## 3. Turn on Vertex AI and the budget API

```bash
gcloud services enable aiplatform.googleapis.com billingbudgets.googleapis.com
```

## 4. Sign your laptop in (Application Default Credentials = the login the code uses)

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project "$GOOGLE_CLOUD_PROJECT"
```

## 5. Budget alert: $10, emails at 50% / 90% / 100%

Emails go to Billing Account admins and users (that is you).

```bash
gcloud billing budgets create --billing-account=ACCOUNT_ID --display-name="civictrace-dev-10usd" \
  --budget-amount=10USD --filter-projects="projects/$GOOGLE_CLOUD_PROJECT" \
  --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0
```

A budget alert is a warning email, not a spending cap. Caps come from instance limits later (Slice 5).

## Verify (read-only; paste the output into MOO-690)

```bash
gcloud config list                                    # shows account + project
gcloud services list --enabled | grep aiplatform     # one line expected
gcloud auth application-default print-access-token | cut -c1-12   # prints a token prefix, no error
gcloud billing budgets list --billing-account=ACCOUNT_ID           # shows civictrace-dev-10usd
git grep -lE "private_key|BEGIN PRIVATE" -- . ":!docs/runbooks/*"   # must print nothing
```

Smoke test: one tiny Gemini Flash call, no CivicTrace data. Expect a JSON reply containing `OK`.

```bash
export CIVICTRACE_MODEL=gemini-2.5-flash    # verified 2026-08-19. gemini-3-flash-preview also works, but only with location=global
curl -s -X POST -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" \
  "https://$GOOGLE_CLOUD_LOCATION-aiplatform.googleapis.com/v1/projects/$GOOGLE_CLOUD_PROJECT/locations/$GOOGLE_CLOUD_LOCATION/publishers/google/models/${CIVICTRACE_MODEL}:generateContent" \
  -d '{"contents":[{"role":"user","parts":[{"text":"Reply with the single word OK."}]}]}'
```

Then copy `.env.example` to `.env` and fill `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `CIVICTRACE_MODEL`. `.env` is gitignored.

## Teardown / revoke

```bash
gcloud auth application-default revoke              # laptop can no longer call Vertex
gcloud billing projects unlink "$GOOGLE_CLOUD_PROJECT"   # stops all spend on the project
gcloud projects delete "$GOOGLE_CLOUD_PROJECT"      # full delete; 30-day undo window
```

Run the last two only after the demo proof is saved. Print the project id and confirm before deleting.
