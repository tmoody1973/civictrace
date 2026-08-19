# CivicTrace Reasoning Visibility UX

## Decision

**Use Vercel AI SDK Elements’ `ChainOfThought` component as a collapsible, source-grounded _Evidence Trace_, not as raw model chain-of-thought.** The component provides a collapsible sequence with labelled steps, descriptions, completion status, and supporting result/image regions, which maps well to CivicTrace’s bounded agent workflow.[1]

CivicTrace should never expose hidden, free-form model deliberation or imply that a model’s internal narrative is evidence. The editor needs an **audit trail**: which approved source was processed, which agent produced a typed proposal, which deterministic check passed or failed, what source anchors support the staged claim, what remains unknown, and where human approval is required.

> **Product copy:** “Evidence Trace” is preferred over “Chain of Thought.” It describes observable workflow and provenance rather than claiming a hidden reasoning transcript is authoritative.

---

## Where It Lives in the Evidence Studio

Place a collapsed **Evidence Trace** directly beneath the Decision Delta header and above the detailed source panes. It should expand on demand and never replace original-source links.

```text
┌─ Decision Delta: Public commitment target date changed ────────────────────┐
│ Verified original and later record | Human review required                 │
│                                                                            │
│ ▸ Evidence Trace · 6 verified workflow steps · 2 source artifacts         │
│                                                                            │
│ [Original promise]       [Later record]        [What remains unknown]     │
│ exact PDF anchor         exact dataset row      “Completion not established”│
└────────────────────────────────────────────────────────────────────────────┘
```

Opening the trace reveals only these safe, user-relevant step types:

| Step | UI label | Safe description | Required link |
|---|---|---|---|
| 1 | **Source preserved** | “Saved the official Legistar attachment; hash and retrieval time recorded.” | Original source / artifact provenance |
| 2 | **Evidence extracted** | “Located a stated target date in page 12.” | Exact PDF page/table/row/timestamp |
| 3 | **Case candidate evaluated** | “Matched the official project number to this Promise Ledger case.” | Entity/case evidence anchors |
| 4 | **Later evidence compared** | “A later record gives a different target date.” | Exact later artifact anchor |
| 5 | **Policy checks passed** | “Original and later anchors present; no blocked data category detected.” | Validator report, not model prose |
| 6 | **Human decision required** | “A narrow next question is staged; no external action will occur without approval.” | Approval drawer/action summary |

Do not show token-level model output, hidden “thoughts,” ungrounded self-confidence, speculative alternatives, raw tool-call arguments containing more data than the user needs, model error tracebacks, or data restricted by source/role policy.

---

## Component Strategy

| UI need | AI SDK Element | CivicTrace behavior |
|---|---|---|
| Collapsible workflow trace | `ChainOfThought`, `ChainOfThoughtHeader`, `ChainOfThoughtContent` | Closed by default for a clean evidence workspace; opens on demand. |
| Workflow milestones | `ChainOfThoughtStep` | Maps to deterministic event/agent/validator milestones; labels and descriptions come from ledger events, not free-form LLM reasoning. |
| Source links | `Sources` / `InlineCitation` where appropriate | Shows canonical source URL and exact anchor beside the step that depends on it. |
| Reviewer gate | `Confirmation` / `Checkpoint` pattern | Makes external-action approval explicit, separate from completed AI work. |
| Agent/workflow status | `Agent`, `Task`, `Tool` patterns if adopted | Shows named system component and `complete`, `active`, or `pending` status; never implies unreviewed output is fact. |

Use only the components that advance CivicTrace’s core verification experience. Do not turn the Evidence Studio into a generic agent-control dashboard.

---

## Backend Contract

The frontend must receive a deterministic `EvidenceTrace` generated from immutable ledger/job events. It must not receive a raw LLM response as the trace.

```ts
export type EvidenceTraceStatus = "complete" | "active" | "pending" | "blocked";

export interface EvidenceTraceSource {
  artifactId: string;
  canonicalUrl: string;
  anchorLabel: string; // e.g. "Agenda PDF · p. 12"
}

export interface EvidenceTraceStep {
  id: string;
  sequence: number;
  kind:
    | "artifact_stored"
    | "evidence_validated"
    | "entity_link_proposed"
    | "case_linked"
    | "delta_validated"
    | "policy_checked"
    | "human_approval_required";
  label: string;
  description: string; // factual workflow statement, rendered from validated fields
  status: EvidenceTraceStatus;
  sourceRefs: EvidenceTraceSource[];
  agentName?: string; // e.g. "Document Evidence Agent"
  validatorResult?: "passed" | "needs_review" | "blocked";
  occurredAt: string;
}

export interface EvidenceTrace {
  traceId: string;
  caseId: string;
  policyVersion: string;
  steps: EvidenceTraceStep[];
}
```

The `description` template is produced by code from validated event data. For example, not “I reasoned that the dates conflict,” but “The Delta Investigator proposed a revised target date; the validator confirmed original and later source anchors.”

---

## Frontend Outline

```tsx
// frontend/src/components/evidence/evidence-trace.tsx
import {
  ChainOfThought,
  ChainOfThoughtContent,
  ChainOfThoughtHeader,
  ChainOfThoughtStep,
} from "@/components/ai-elements/chain-of-thought";

export function EvidenceTrace({ trace }: { trace: EvidenceTrace }) {
  const completed = trace.steps.filter((step) => step.status === "complete").length;

  return (
    <ChainOfThought defaultOpen={false} aria-label="Evidence processing trace">
      <ChainOfThoughtHeader>
        Evidence Trace · {completed}/{trace.steps.length} completed
      </ChainOfThoughtHeader>
      <ChainOfThoughtContent>
        {trace.steps.map((step) => (
          <ChainOfThoughtStep
            key={step.id}
            label={step.label}
            description={step.description}
            status={step.status === "blocked" ? "pending" : step.status}
          >
            <EvidenceAnchorList sourceRefs={step.sourceRefs} />
            {step.validatorResult && <ValidatorState value={step.validatorResult} />}
          </ChainOfThoughtStep>
        ))}
      </ChainOfThoughtContent>
    </ChainOfThought>
  );
}
```

Adapt the exact import path to the AI Elements installation. The key implementation constraint remains: UI step data comes from `GET /cases/{caseId}/evidence-trace`, which reads the ledger; it does not read a model “reasoning” field.

---

## Acceptance Criteria

1. The trace is collapsed by default and keyboard accessible.
2. Every completed material step links to at least one precise original source anchor.
3. A `blocked`, `not published`, or `needs review` state remains visible; it may not be rendered as `complete`.
4. The trace never exposes raw model private reasoning, hidden prompts, secrets, or unapproved source content.
5. The human approval step remains visually and functionally distinct from all completed system steps.
6. A reviewer can move from any visible trace step to the original artifact in no more than one interaction.

## References

[1]: https://elements.ai-sdk.dev/components/chain-of-thought "AI SDK Elements — Chain of Thought"
