# Issue tracker

CivicTrace tracks work in three places. Pick by the kind of work.

| Kind of work | Where | How |
| --- | --- | --- |
| Planned, multi-step, load-bearing build work (features, phases, milestones) | **Linear** — team `Moodyco` | `/linear-build` skill and the `mcp__plugin_linear-build_linear-server__*` tools |
| Quick scratch work, solo notes, PRD drafts before they are real | **Local markdown** — `.scratch/<feature-slug>/` | plain files, see below |
| Public bug reports / external contributors | **GitHub Issues** — only once this repo has a `git remote` on GitHub | `gh` CLI |

Default when unsure: Linear for anything that will take more than one session; `.scratch/` for anything smaller.

## Linear (primary for build work)

- Team: `Moodyco`. Resolve ids with `list_teams` / `list_projects` / `list_issue_labels`; never guess an id.
- Every issue carries the issue-as-spec contract: `## Intent`, `## Acceptance criteria`, `## Verification checklist`, `## Out of scope`.
- **Create an issue**: `create_issue` (title, description, team, optional `project`, labels).
- **Read an issue**: `get_issue` with the `MOO-123`-style identifier.
- **List**: `list_issues` filtered by team/project/status/label; `list_my_issues` for "what's next".
- **Comment**: `create_comment`. Verification evidence goes here.
- **Triage state**: Linear labels named per `triage-labels.md`. Create missing labels with `create_issue_label` on first use.
- Commits reference the identifier: `feat(scope): short description (MOO-42)`.

## Local markdown (`.scratch/`)

- One feature per directory: `.scratch/<feature-slug>/`
- The PRD is `.scratch/<feature-slug>/PRD.md`
- Implementation issues are `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`
- Triage state is a `Status:` line near the top of each issue file (role strings in `triage-labels.md`)
- Comments append under a `## Comments` heading at the bottom
- `.scratch/` is local scratch. Add it to `.gitignore` if it should not ship.

## GitHub (when a remote exists)

Not active yet — this repo has no `.git` directory and no remote. Once it does:

- **Create**: `gh issue create --title "..." --body "..."` (heredoc for multi-line bodies)
- **Read**: `gh issue view <number> --comments`
- **List**: `gh issue list --state open --json number,title,body,labels,comments`
- **Comment**: `gh issue comment <number> --body "..."`
- **Labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

## When a skill says "publish to the issue tracker"

Use the table above. If the work is a planned build item, create a Linear issue (offer `/linear-build`). Otherwise create a file under `.scratch/<feature-slug>/`. Use GitHub only if the user asks for a public issue and a remote exists.

## When a skill says "fetch the relevant ticket"

- `MOO-123` / `TEAM-123` style id → `get_issue` in Linear.
- A path → read the file under `.scratch/`.
- A bare number with a GitHub remote → `gh issue view <number> --comments`.
