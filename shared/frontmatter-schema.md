# Frontmatter Schema

Single source of truth for all artifact metadata in this project.

## Common Fields

Every artifact includes these fields (one exception: `phase` docs omit `tags` and `related` — they inherit the plan's):

```yaml
title: "Human-readable title"
type: research | brainstorm | spec | design | plan | phase | debrief | retro | diagram | decision-log | review
status: <type-specific, see below>
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
related: [Specs/FeatureName, Research/topic-slug.md]
```

`related` entries are planning-root-relative: use the **directory** path for specs, designs, and plans (`Specs/FeatureName`, `Designs/ComponentName`, `Plans/PlanName`), and the **file** path for flat artifacts (`Research/topic-slug.md`, `Brainstorm/topic-slug.md`). Legacy `Retro/YYYY-MM-DD-slug.md` and `Diagrams/slug.md` references remain valid for read compatibility, but the compact core does not create them. Consumers that need the document behind a directory entry append `/README.md`.

Any artifact may additionally declare an optional `refresh_when` field — a list of event-shaped trigger descriptions that force a refresh (e.g., `refresh_when: ["dependency X ships v3", "Specs/Payments changes", "vendor answers the webhooks question"]`). Lifecycle skills honor known-fired triggers; broad stale-artifact gardening is outside the compact core.

## Status Values by Type

| Type | Statuses |
|------|----------|
| research | `draft`, `active`, `archived` |
| brainstorm | `draft`, `active`, `archived` |
| spec | `draft`, `review`, `approved`, `implemented`, `superseded` |
| design | `draft`, `review`, `approved`, `implemented`, `superseded` |
| plan | `draft`, `approved`, `active`, `complete`, `archived` |
| phase | `planned`, `in-progress`, `complete`, `blocked`, `deferred` |
| task | `planned`, `in-progress`, `complete`, `blocked`, `deferred` |
| debrief | `draft`, `complete` |
| retro (legacy) | `draft`, `complete` |
| diagram (legacy) | `draft`, `active`, `archived` |
| decision-log | `active`, `archived` |
| review | `open`, `resolved`, `superseded` |

## Stable Identifiers & Traceability

Numbered elements carry stable, per-document identifiers so artifacts can cite each other precisely and reconciliation is greppable:

| Element | Id format | Lives in |
|---|---|---|
| Functional requirement | `FR-NN` | spec Requirements |
| Non-functional requirement | `NFR-NN` | spec Requirements |
| Acceptance criterion | `AC-NN` | spec Acceptance Criteria |
| Phase / task | `N` / `N.M` | plan frontmatter (existing convention) |
| Decision | `D-NNNN` | decision ledger |
| Review finding | `F-NN` | review artifact |
| Review follow-up | `FU-NN` | review artifact |

Rules:

- **Ids are append-only and never renumbered.** Removing an item leaves its id retired (strike the line or note "removed — see <reason/citation>") so existing cross-references never silently re-bind to a different item.
- **Cross-reference by id.** A plan task's `verification` (or its body section) names the `AC-NN`/`FR-NN` ids it satisfies; a design section that realizes a requirement cites its `FR-NN`; governed sections cite ledger ids (`D-NNNN`) per `shared/decision-log.md`. These citations are what make drift detectable — without them every reconciliation check is blind.
- **Changing a numbered element is a reconciliation event**: after editing it, grep the other artifacts for its id and update or flag every citing site (same pattern as the decision ledger's supersession cascade). `sdd-validate` audits for unnumbered elements and dangling id citations.

## Review Artifact Schema

A review artifact (`<target-home>/reviews/…`, type `review`) carries `findings[]` and `followups[]` frontmatter arrays — the machine layer for review tracking. Entry fields, location/naming, the Resolution Log, disposition rules, and follow-up tracking are defined in `shared/review-artifacts.md` — the single source of truth for this artifact.

Per-finding statuses (entry-level, not artifact statuses): `open`, `fixed`, `deferred`, `rejected`, `answered`. The artifact is `resolved` only when no finding is `open`; `superseded` links to the newer review of the same target.

## Decision Ledger Schema

The decision ledger (`Decisions/decisions.md`, type `decision-log`) carries a `decisions[]` frontmatter array — the same structured-list convention as `phases[]`/`tasks[]`. Entry fields, lifecycle rules (append-only; accepted entries mutate only via `status` + `superseded_by`), the collision procedure, and distribution rules are defined in `shared/decision-log.md` — the single source of truth for this artifact.

Per-entry statuses (these are entry-level fields inside `decisions[]`, **not** artifact `type` statuses — the ledger artifact itself is only ever `active` or `archived`): `proposed`, `accepted`, `rejected`, `superseded`. `rejected` entries are kept as negative truths, never deleted.

## Plan Schema

### Plan README.md

```yaml
---
title: "Plan Title"
type: plan
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
related: [Specs/FeatureName, Designs/ComponentName]
phases:
  - id: 1
    title: "Phase Title"
    status: planned
    doc: "01-Phase-Title.md"
  - id: 2
    title: "Phase Title"
    status: planned
    doc: "02-Phase-Title.md"
    depends_on: [1]
---
```

Body contains: Overview, Architecture, Key Decisions, Dependencies, Plan Completion Evidence, and Open Questions (omit when empty — a plan cannot be `approved` while an in-scope question is unanswered).
No status tables in the body — phases are read from frontmatter.

`## Plan Completion Evidence` follows `shared/completion-evidence.md`. It is
required from plan creation onward and contains `Pending — not complete.` until
the plan is eligible to transition to `complete`.

### Phase Doc (01-Phase-Title.md)

```yaml
---
title: "Phase Title"
type: phase
plan: PlanName
phase: 1
status: in-progress
created: YYYY-MM-DD
updated: YYYY-MM-DD
deliverable: "What this phase delivers"
tasks:
  - id: "1.1"
    title: "Task title"
    status: planned
    verification: "How we know this task is good and complete"
  - id: "1.2"
    title: "Task title"
    status: planned
    depends_on: ["1.1"]
    verification: "Specific criteria to confirm correctness"
---
```

#### Task Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Task identifier (e.g., "1.1") |
| `title` | yes | Human-readable task title |
| `status` | yes | Task status (see status values above) |
| `depends_on` | no | List of task IDs this task depends on |
| `verification` | yes | How we know the work is good and complete — name each new or changed behavior to cover, not test counts. Where the check is commandable, include the exact command and expected observable output (e.g., `cargo test auth:: — 14 pass incl. the new refresh-expiry case`); prose-only criteria are for behavior no command can observe. The task is also the normal implementation-commit boundary: it must be a complete, independently bisectable feature slice that leaves the repository buildable and its named checks passing (D-0012). |

Body contains task detail sections keyed by task ID as headings:

```markdown
## 1.1: Task Title

### Subtasks
- [ ] Subtask one
- [ ] Subtask two

### Notes
Implementation notes, including the complete feature/capability that defines
this task's clean bisectable commit boundary (D-0012)...

### Completion Evidence
Pending — not complete.

### Trap
Optional — only for tasks with a known tempting-but-wrong shortcut. Names
the shortcut a hasty implementer would take and why it's wrong. `sdd-implement`
passes it verbatim to the implementer's dispatch.
```

Every task section also contains `### Completion Evidence`, and every phase
contains `## Phase Completion Evidence` after its Acceptance Criteria. Both
follow `shared/completion-evidence.md`. Prospective task `verification` is not
completion evidence; the evidence section records what actually ran. Missing
or pending evidence forbids a `complete` transition.

## Debrief Schema

Debriefs live at `Plans/<PlanName>/notes/<NN>-Phase-Name.md` and add three fields to the common set:

```yaml
---
title: "Phase N Debrief: Phase Title"
type: debrief
status: complete        # draft while being written incrementally
plan: PlanName          # the plan directory name
phase: 1                # the phase number this debrief covers
phase_title: "Phase Title"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: []
related: []
---
```

## Status Color Coding

Legacy diagrams and inline Mermaid renderers may use this status styling (`classDef` colors):

- `complete` / `approved` / `implemented` -> green
- `in-progress` / `active` / `review` -> amber
- `planned` / `draft` -> gray
- `blocked` -> red
- `deferred` / `archived` / `superseded` -> muted
