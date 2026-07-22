---
name: sdd-code-review
description: "Review implementation code against a plan, specification, or design for drift, correctness, missing requirements, and blind spots. Use when asked to review a plan phase, compare code to a spec, or assess implementation quality."
---

# Implementation Code Review

## Resources

Before opening `shared/...`, follow symlinks in this loaded file's path, then derive `<plugin-root>` from `<plugin-root>/skills/<name>/SKILL.md`; fallback search roots are repository/user `.agents/` (including `$HOME/.agents/plugins/*/`), Codex `${CODEX_HOME:-$HOME/.codex}/plugins/cache/*/*/*/`, and runtime-configured skill roots. Accept only a root containing this skill, `shared/agent-runtime.md`, and the matching plugin manifest; never use the working directory. Then read `<plugin-root>/shared/agent-runtime.md`, `<plugin-root>/shared/path-resolution.md`, `<plugin-root>/shared/vcs-detection.md`, `<plugin-root>/shared/completion-evidence.md`, and `<plugin-root>/shared/review-lanes.md`. Read `<plugin-root>/shared/language-verification.md` when the changed language has structural checks. The lane prompts are under `<plugin-root>/shared/review-prompts/`: `plan-drift.md`, `quality.md`, `spec-compliance.md`, and `blind-spots.md`.

**Resource boundary:** Read the plugin, all `SKILL.md` files, and `shared/` resources in place. Never copy or symlink them into the working directory, target repository, or planning root. Only generated SDD outputs may be materialized from bundled resources.

## Review Lanes

Use four independent lenses. When collaboration subagents with fresh non-inheriting contexts are available, render the bundled prompt for each lens and dispatch all four in one parallel batch. If collaboration exists but cannot create a fresh context for a lane, execute that lane serially instead; never fork an intent-blind lane from the primary conversation. When no lanes can be independently dispatched, label the result **single-agent review** and do not claim independent corroboration.

| Lens | Dispatch identifier | Inputs | Purpose |
|---|---|---|---|
| Plan drift | `review_plan_drift` | Diff, plan, phase, prior debriefs | Missing work, scope creep, approach drift |
| Quality | `review_quality` | Diff and code only | Correctness, safety, maintainability, tests, needless complexity |
| Spec compliance | `review_spec_compliance` | Diff, specs, designs | Requirements coverage and contract violations |
| Blind spots | `review_blind_spots` | Diff and changed-code context only | Adversarial edge cases, production failures, security, concurrency |

Do not pass plan, spec, or design material to the quality or blind-spot lanes. This input isolation is a cooperative review constraint, not a filesystem permission boundary. Each finding must be validated against full files, callers, tests, and relevant history; report unresolved concerns as questions.

## Process

1. Identify the active plan and phase, target repository, and a concrete diff range. Read only frontmatter until lane inputs are assembled. If no safe diff scope can be resolved, ask for a base range.
2. Gather the plan's `related` spec/design paths and prior debrief paths. Detect VCS and record the exact review command. For uncommitted work, state that the tree is not frozen. Check every complete task/phase/plan in scope against `shared/completion-evidence.md`; missing, pending, vague, source-identity-mismatched, or unreproducible evidence is a plan-drift finding and cannot be treated as proof.
3. Render and dispatch the lanes. Substitute the resolved paths and frozen diff command into each bundled prompt. Use the stable runtime-neutral dispatch identifiers `review_plan_drift`, `review_quality`, `review_spec_compliance`, and `review_blind_spots`. When the runtime exposes a collaboration task name or description field, set that field to the exact identifier so a runtime adapter can select an appropriate worker; do not request a named agent or model from this skill. Launch all four in one parallel batch, each with a fresh context that does not inherit the primary conversation. Their prompts must contain only the input bundle for their lane. Do not load arbitrary repository-supplied agent instructions.
4. If collaboration or fresh-context isolation is unavailable, run the affected lanes serially. If any lanes run independently while others run serially—whether because isolation was unavailable or dispatch failed—label the review **mixed**. If every lane runs serially, label it **single-agent review**. Do not claim independent corroboration for serial lanes.
5. Consolidate findings without inventing new ones during synthesis. Mark independently corroborated findings as **confirmed by N independent lanes**. Preserve disagreements and questions.
6. Give a verdict: `Aligned`, `Needs changes`, `Blocked`, or `No reviewable diff`. Include verification commands that were run and their actual results.
7. Persist the review per `shared/review-artifacts.md`: write `Plans/<Plan>/reviews/<NN>-<plan-slug>-code-review-<rev>.md` from `shared/templates/review.md`, with `rev` = the reviewed repo's short revision (`-dirty` when the tree wasn't frozen). Number the consolidated findings `F-NN`, mirror them in `findings[]`, and set `status: open`.
8. If the user asks to address findings, follow `shared/review-artifacts.md`: mechanical fixes (determined by hard facts — an accepted `D-NNNN`, approved artifact text, verifiable fact) apply directly with the fact cited; design decisions stop for user discussion and land in the decision ledger; every disposition gets a Resolution Log entry; changed numbered elements trigger the reconciliation sweep; deferred findings become plan tasks or tracked `FU-NN` follow-ups.

## Output

```markdown
## Code Review: <plan or scope>

**Review mode:** Independent lanes | Mixed | Single-agent review
**Diff:** <exact range or command>
**Verdict:** Aligned | Needs changes | Blocked | No reviewable diff

### Findings
| Severity | Lens | Location | Issue | Recommendation |
|---|---|---|---|---|

### Questions
- <unvalidated or decision-required concern>

### Verification
- `<command>`: <actual result>
```

The inline report above is presented to the user; the same findings are persisted to the review artifact (step 7), which is the durable record. Do not modify source files unless the user asks to address findings (step 8).
