# SDD Planner Skills

`sdd-planner` is a runtime-neutral agent-skills plugin for spec-driven development. It creates and maintains Markdown planning artifacts with YAML frontmatter for research, specifications, designs, implementation plans, code review, debriefs, and validation.

Every capability is a plain `SKILL.md` skill with shared resources under `shared/` — no slash commands, named subagent types, runtime hooks, or model-specific instructions — so it works in any agent runtime that discovers `SKILL.md` skills, with any model. Public skill names use the `sdd-` prefix (`sdd-plan`, `sdd-implement`, `sdd-code-review`, and so on) to avoid collisions in global skill directories (D-0004):

`sdd-code-review` exposes stable semantic identifiers for its four independent
review lanes. Runtime adapters may map those identifiers to specialized workers
or models, but the skill never names or depends on them and retains its serial
single-agent fallback (D-0008).

`sdd-implement` uses the stable runtime-neutral implementation dispatch
identifier `implement_task` when a runtime task name or description field is
available. Runtime adapters may select a worker without the skill requesting an
agent or model, and the primary-agent fallback remains transparent (D-0009).

- **OpenCode**: point a skills discovery path at this repository (for example `ln -s <this-repo> ~/.agents`, so the skills resolve as `~/.agents/skills/<name>/SKILL.md`), or mount it there in a container.
- **Codex**: install via the `codex-marketplace` repository, then install `sdd-planner` from it. Start a new thread after installation so the skills are available.
- Any other runtime that loads the `.agents/skills` convention or directory-sourced skills works the same way.

Ask your agent for a workflow naturally: "set up spec-driven planning in this repository", "write a specification for this feature", or "review this implementation against the active plan."

Planning artifacts live in the root configured by `planning-config.json`. The plugin uses `AGENTS.md` for optional repository guidance and does not create tool-specific files or launchers.

Tasks, phases, and plans carry durable completion-evidence sections recording
the exact commands, tools, context, revision, and observed results used to
justify each `complete` transition (D-0005).

Plan tasks are the smallest complete dependency-ordered native SCM
revision/checkpoint boundaries: each is a clean, cohesive, independently
bisectable feature or internal capability, while subtasks remain mechanical
steps inside it (D-0014, D-0015). Every completed task receives a focused review
of its complete diff before its revision is finalized, and lifecycle recording
preserves its complete state. **Git adapter:** `sdd-implement` verifies and
commits that slice before recording evidence against the immutable feature
commit, then commits lifecycle bookkeeping separately. Native SCM is the sole
source identity: dirty Git, no-SCM, and unsupported SCM adapters cannot mark
work complete (D-0018).

Phase completion freezes a concrete revision/range and requires a persisted
`Aligned` run of all four `sdd-code-review` lanes. Needs changes or Blocked
prevents completion; every material review-driven change gets a new planned
task id and complete task revision, even when small, then a fresh full review
until the final phase state is materially unchanged (D-0014).

Completed Git task evidence records `git show <full40>` for final-commit review
or `git diff <full40>..<full40>` for range review of the complete task diff, its
exact reviewed candidate/final native SCM identity or diff, and a
`PASS/Aligned` result. Final phase-review evidence uses `- Final aligned review:
<artifact path>; frozen: <exact rev>`, with exact equality to the review's
frontmatter `rev`. **Git lifecycle adapter:** the cited review artifact must be
committed at planning-root `HEAD`; Perforce and no-SCM planning roots currently
have no validated durable lifecycle adapter and must leave entities non-complete.

The compact core exposes: `sdd-setup`, `sdd-research`, `sdd-brainstorm`,
`sdd-specify`, `sdd-design`, `sdd-plan`, `sdd-implement`, `sdd-code-review`,
`sdd-poke-holes`, `sdd-debrief`, `sdd-decide`, `sdd-decision-log`, and
`sdd-validate` (D-0006). Codebase excavation is a mode of `sdd-research`;
diagramming, retrospectives, and generic simplification are outside the core.

`sdd-validate` runs `scripts/sdd_validate.py` for deterministic artifact
integrity checks before applying model judgment to semantic sufficiency. The
script requires PyYAML as declared in `requirements.txt` and supports text or
JSON diagnostics suitable for local use and CI.

Decision-ledger writes additionally run
`scripts/sdd_decision_validate.py <ledger>`, a focused read-only validator for
ledger format, archives, entry types and ids, supersession integrity,
structural collision candidates, and accepted-entry immutability (D-0010).
