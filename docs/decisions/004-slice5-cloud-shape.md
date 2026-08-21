# 004 — The shape of the cloud demo: local screen, minimal BigQuery, one shared key

Slice 5 put CivicTrace in Google Cloud for real. Three judgment calls shaped it. Each could have gone another way.

## Call 1 — The demo screen runs on the laptop, not on a hosted website

- **Decision** — The Evidence Studio (the screen) stays a local app on Tarik's laptop. Only the backend lives in the cloud; the screen talks to it over the public URL.
- **Why this came up** — 2026-08-20. The judges must see a cloud-deployed system. Hosting the screen too (on Vercel or Cloud Run) sounds more "finished," but it adds a sign-in system, a second deploy pipeline, and a second thing that can break on demo day.
- **Options**
  1. *Local screen, cloud backend* — one deploy to protect, the demo machine is in our hands. Risk: a judge may ask "why isn't the UI hosted?"
  2. *Host the screen too* — looks complete. Cost: real user sign-in becomes mandatory (a shared key in a public website is a leak), roughly a day of work with new failure modes.
- **What we chose and why** — Option 1. Joint call, Claude recommended. The hackathon rule is that the *backend* must be deployed; the screen is presentation. Every hour saved went into proving the evidence pipeline in the cloud.
- **What we gave up** — The "try it yourself" link. Nobody outside this laptop can click the demo.
- **How we'll know if this was right** — The demo video shows the full click-through against live cloud data without a hosted-UI outage risk, and no judge scores us down for it.
- **What actually happened** — _(Tarik fills this in later.)_

## Call 2 — BigQuery is in, but minimal — and it must actually do a job

- **Decision** — One BigQuery table holds the reviewed corpus list (4 rows). The cloud worker asks BigQuery for each event's row before any AI agent runs; no row means the event is refused. That is BigQuery's whole job.
- **Why this came up** — 2026-08-20. The hackathon rewards using Google's data stack, but bolting on a big warehouse for 4 documents would be decoration. The honest middle: small, but load-bearing.
- **Options**
  1. *No BigQuery* — honest for 4 rows, but the architecture shows no path for the real corpus (thousands of city records), and the stack story is weaker.
  2. *Minimal and honestly used* — a real gate in the pipeline, one table, near-zero cost. Risk: a reviewer calls 4 rows theater.
  3. *Full corpus in BigQuery* — the real end-state, but there is no full corpus yet; we'd be building for data we don't have.
- **What we chose and why** — Option 2. Tarik's call. The table is the same *shape* the citywide corpus would use, and the worker genuinely depends on it — the query jobs are visible in the Console, one per event.
- **What we gave up** — Simplicity: the worker now needs BigQuery to be up (a failed lookup refuses the event safely and retries — it never guesses).
- **How we'll know if this was right** — The Console shows the worker's own query per event, and an event not on the reviewed list is refused before any agent sees it. Both were proven live on 2026-08-20.
- **What actually happened** — _(Tarik fills this in later.)_

## Call 3 — A public API address guarded by one shared key, not a private network

- **Decision** — The backend API has a public URL. Every request must carry one shared secret key (a "bearer token") that lives only in Google's Secret Manager and one git-ignored file on the laptop. The worker, by contrast, is fully private (Google-identity only).
- **Why this came up** — 2026-08-20. The laptop screen must reach the cloud API. A private-network setup (proxy or tunnel) is the textbook answer but adds moving parts we would be debugging on demo day.
- **Options**
  1. *Public URL + shared key* — simple, demoable from anywhere, honest about what it is (a demo gate, not user accounts). Risk: one key means one leak exposes the API — which is why it is never committed and the AI-capable worker doesn't accept it at all.
  2. *Private-only with a proxy/tunnel* — stronger posture, no public surface. Cost: extra infrastructure, and a tunnel hiccup can kill the live demo.
- **What we chose and why** — Option 1. Joint call. The blast radius is small by design: the API holds no AI access (that permission simply doesn't exist on its service account), writes only draft files, and the key rotates in one command.
- **What we gave up** — Real per-person accounts and audit-by-identity. The drawer says so on screen: "Identity is a typed name for now; sign-in arrives with the cloud deploy."
- **How we'll know if this was right** — The key never appears in the repo or CI (checked), a request without it gets a 401 (proven), and a leaked-key drill is one `gcloud` rotate command. Post-hackathon, this decision expires: real sign-in replaces the shared key before any second user exists.
- **What actually happened** — _(Tarik fills this in later.)_
