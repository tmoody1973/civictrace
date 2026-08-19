# Evidence, Privacy, and Editorial Integrity Rules

CivicTrace is a public-interest evidence system. It supports civic reporting and research; it does not act as a prosecutor, surveillance system, public-records filing bot, or student-risk system.

## Evidence Integrity

Every material factual statement must trace to a supplied original public source artifact and a precise anchor such as document page, table row/cell, JSON field, transcript span, media timestamp, or map feature. Keep the raw artifact immutable in Cloud Storage and store the source URL, source ID, content hash, retrieval time, extraction version, and any source-access limitation.

A Decision Delta requires both an original commitment anchor and later evidence anchor. If the record is incomplete, delayed, contradictory, inaccessible, or ambiguous, use an explicit state: `UNKNOWN`, `NOT_PUBLISHED`, `CONFLICTING`, `CANDIDATE_LINK`, `REQUEST_NEEDED`, or `HUMAN_REVIEW`. Do not make a plausible inference to fill a gap.

Do not assert misconduct, fraud, corruption, negligence, legality, political motive, intent, or causation unless an explicit, reliable source provided in the case establishes that exact point. Do not turn a speaker comment into an institutional decision. Do not treat a diarization label as a person’s name or identity.

## Public-Source and MPS Privacy Boundary

Use only allowlisted public sources and public institutional evidence. For MPS, permitted materials include public Board agendas, minutes, policy documents, public meeting audio/video, school improvement plans, public budgets/contracts/facility material, and public aggregate district/school report cards.

Never ingest, index, log, display, infer, or generate outputs about individual student attendance, grades, discipline, disability, health, family, home address, student records, or other personally identifying/sensitive information. Do not build student prediction, scoring, intervention, or profiling features.

## Human Approval Boundary

Agents may retrieve permitted public sources, extract evidence, compare records, propose questions, and prepare drafts. Agents may not publish, email, contact an official, file a public-records request, submit a form, or otherwise communicate externally.

Any external-ready artifact must have a human approval token that binds the exact case, artifact hash, action type, destination where relevant, reviewer identity, and expiration. The artifact worker must fail closed when this approval is missing, mismatched, expired, or revoked.

## Product Language

Use neutral, source-grounded phrasing. Prefer “the public record states,” “the record does not establish,” “the later document revises,” and “the next expected evidence is.” Avoid language that presents a model’s interpretation as final truth.
