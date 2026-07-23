---
title: "{{TITLE}}"
type: phase
plan: "{{PLAN}}"
phase: {{PHASE_NUM}}
status: planned
created: {{DATE}}
updated: {{DATE}}
deliverable: "{{DELIVERABLE}}"
tasks: []
# Each task entry should include:
#   id: "X.Y"
#   title: "Task title"
#   status: planned
#   verification: "How we know this complete, bisectable task revision passes"
#   depends_on: ["X.Z"]  # optional
---

# Phase {{PHASE_NUM}}: {{TITLE}}

<!-- sdd-validate format contract:
- Store this document as UTF-8 with LF line endings and keep the YAML
  frontmatter as a mapping between standalone `---` delimiters.
- Keep `title`, `type`, `status`, `created`, and `updated`; use a phase status
  of `planned`, `in-progress`, `complete`, `blocked`, or `deferred`; dates use
  `YYYY-MM-DD`. Task status uses the same vocabulary.
- `plan`, `phase`, and `deliverable` are required. `tasks` is a YAML list of
  mappings; each task requires nonempty `id`, `title`, `status`, and
  `verification`. Task IDs are unique within the plan and use exactly
  `<phase>.<digits>`; status uses the task status vocabulary.
- Optional `depends_on` is a YAML list of task IDs from this plan. It contains
  no unknown IDs, self-dependencies, or dependency cycles.
- Every task mapping has one matching H2 beginning `## <task-id>:` (a space in
  place of the colon is also accepted) with exact H3 headings `Subtasks`,
  `Notes`, and `Completion Evidence` inside it.
- Each task is one clean, complete, independently bisectable native SCM
  revision/checkpoint boundary (D-0014, D-0015). Its subtasks are mechanical
  steps inside that boundary; the repository remains buildable and named
  verification passes when the task lands. `Notes` states the complete
  behavior/capability delivered at the boundary and excludes unrelated feature
  slices. Clearly labeled Git adapter guidance may call that revision a commit;
  governing workflow language must not assume every SCM has Git commits.
- FR-NN, NFR-NN, AC-NN, and D-NNNN citations must resolve through the plan's
  `related` graph and applicable decision ledger. For approved/active/complete
  plans, task verification/detail and phase Acceptance Criteria collectively
  cite every requirement and acceptance criterion from every related spec.
- A complete phase has only complete tasks, no unchecked `- [ ]` Acceptance
  Criteria, and populated task and phase completion evidence. Phase evidence
  uses one `### Task <id> Evidence Rollup` block per task and repeats that task's
  Completion Evidence body verbatim in its block; complete plan evidence uses
   one labeled phase/task rollup block per child and repeats every child
  command/tool evidence row exactly in the associated block. It also cites a
   persisted final `Aligned` phase review run across all four sdd-code-review
    lanes against a frozen concrete revision/range. Needs changes or Blocked
    forbids completion; every material post-review code fix gets a new planned
    task id and complete task revision before a fresh full four-lane review.
-->

## Overview
Brief description of what this phase delivers.

## {{PHASE_NUM}}.1: {{TASK_TITLE}}

### Subtasks
- [ ] {{SUBTASK}}

### Notes
Revision boundary (D-0014, D-0015): {{COMPLETE_BEHAVIOR_OR_CAPABILITY_THIS_TASK_LANDS}}
### Completion Evidence

<!-- Keep the exact pending line until completion. Populated evidence uses the
exact labels and table formats stated under Phase Completion Evidence below. -->
Pending — not complete.

<!-- Optional per task — include only when the task has a known tempting-but-wrong shortcut:
### Trap
{{THE_SHORTCUT_A_HASTY_MODEL_WOULD_TAKE_AND_WHY_IT_IS_WRONG}}
-->

## Acceptance Criteria
- [ ]

## Phase Completion Evidence

<!-- Keep the exact `Pending — not complete.` line until completion. Evidence
uses the exact labels `Verified`, `Repository`, `VCS`, `Revision / checkpoint`,
and `Identity recheck`, each as `- <label>: <value>`.
`Verified` is `YYYY-MM-DD`; `Repository` is the exact resolved target root;
`VCS` is `git`, `git-worktree`, `perforce`, or `none`; record the tested native
SCM revision/checkpoint. Git adapter: `Revision / checkpoint` is a full 40-hex
implementation commit; commit the feature slice before recording evidence, then
commit only lifecycle/evidence bookkeeping separately. Normal Git completion
creates no snapshot, projection, content-object, or `evidence/` folder. Only
fallback dirty Git, Perforce, or no-VCS identity adds
`Fallback reason`, `Evidence exclusions`, `Governing intent`, `Ignored inputs`,
`Directory inputs`, and `Content snapshot`; dirty Git uses a full base suffixed
`-dirty`. `Fallback reason` names the specific VCS or authorization constraint.
Perforce and no-SCM planning roots may retain fallback handoff evidence but have
no validated durable lifecycle adapter, so they must remain non-complete.
`Governing intent` uses `<64-hex SHA-256> at <durable path>; inputs:
<comma-separated artifact paths and decision ids>`. `Ignored inputs` and
`Directory inputs` use
`none with <inspection basis>` or
`paths: <comma-separated repository-relative paths>; <digests/basis>`.
The exact table columns are
`Command | Working directory | Result | Observable evidence` or
`Tool / inspection | Context | Result | Observable evidence`. Command results
use `PASS (exit 0)`; tool/inspection results use `PASS`. `Identity recheck`
names the tool, an ISO date/time through minutes, and a matched/matching
identity. Follow shared/completion-evidence.md for identity, rollup, review
gate, and durability rules. On phase completion, add `- Final aligned review:
<persisted review artifact path>; frozen: <revision/range>` for the final
`Aligned`, four-lane review; `frozen` must exactly equal that review's `rev`.
For each completed task, also add `Focused review` in strict syntax: for Git,
exactly `git show <full40>` for final-commit review or `git diff
<full40>..<full40>` for range review in backticks before `; complete task diff
reviewed for correctness, scope, tests, maintainability, and task boundary`, then
`Reviewed candidate / final` with the exact native SCM identity (Git adapter:
the task full commit or `diff: <full40>..<full40>` whose distinct base is that
task commit's direct first parent and whose endpoint is that revision; the
command has no extra operands), and
`Review result: PASS/Aligned`. -->
Pending — not complete.
