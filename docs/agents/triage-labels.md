# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue trackers. This repo uses the defaults.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

## Where the label lives

- **Linear** (team `Moodyco`): a team issue label with the exact string above. All five exist as of 2026-08-19. Existing priority labels (`P0`, `P1`, `P2`, `cuttable`, `protected`) and type labels (`Bug`, `Feature`, `Improvement`) stay as they are; triage labels sit alongside them.
- **Local markdown** (`.scratch/`): a `Status: <label>` line near the top of the issue file.
- **GitHub** (when a remote exists): a repo label with the exact string above.

Edit the right-hand column to match whatever vocabulary you actually use.
