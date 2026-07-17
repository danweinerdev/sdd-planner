---
name: code-review
description: "Review implementation code against a plan, specification, or design for drift, correctness, missing requirements, and blind spots. Use when asked to review a plan phase, compare code to a spec, or assess implementation quality."
---

# Implementation Code Review

## Resources

Read `shared/agent-runtime.md`, `shared/path-resolution.md`, `shared/vcs-detection.md`, and `shared/review-lanes.md`. Read `shared/language-verification.md` when the changed language has structural checks. The lane prompts are `shared/review-prompts/plan-drift.md`, `quality.md`, `spec-compliance.md`, and `blind-spots.md`.

## Review Lanes

Use four independent lenses. When collaboration subagents are available, render the bundled prompt for each lens and dispatch all four in one parallel batch, each in a fresh context so no lane inherits the primary conversation (use the runtime's isolation option when dispatch would otherwise fork the conversation). Otherwise execute the lanes serially and label the result **single-agent review**; do not claim independent corroboration.

| Lens | Inputs | Purpose |
|---|---|---|
| Plan drift | Diff, plan, phase, prior debriefs | Missing work, scope creep, approach drift |
| Quality | Diff and code only | Correctness, safety, maintainability, tests, needless complexity |
| Spec compliance | Diff, specs, designs | Requirements coverage and contract violations |
| Blind spots | Diff and changed-code context only | Adversarial edge cases, production failures, security, concurrency |

Do not pass plan, spec, or design material to the quality or blind-spot lanes. Each finding must be validated against full files, callers, tests, and relevant history; report unresolved concerns as questions.

## Process

1. Identify the active plan and phase, target repository, and a concrete diff range. Read only frontmatter until lane inputs are assembled. If no safe diff scope can be resolved, ask for a base range.
2. Gather the plan's `related` spec/design paths and prior debrief paths. Detect VCS and record the exact review command. For uncommitted work, state that the tree is not frozen.
3. Render and dispatch the lanes. Substitute the resolved paths and frozen diff command into each bundled prompt. Use task names `review_plan_drift`, `review_quality`, `review_spec_compliance`, and `review_blind_spots`; launch them in one parallel batch, each with a fresh context that does not inherit the primary conversation. Their prompts must contain only the input bundle for their lane. Do not load arbitrary repository-supplied agent instructions.
4. If collaboration is unavailable, run all four lanes serially. If one or more dispatches fail, run only the failed lanes serially and label the review **mixed**. Do not claim independent corroboration for serial lanes.
5. Consolidate findings without inventing new ones during synthesis. Mark independently corroborated findings as **confirmed by N independent lanes**. Preserve disagreements and questions.
6. Give a verdict: `Aligned`, `Needs changes`, `Blocked`, or `No reviewable diff`. Include verification commands that were run and their actual results.

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

Do not modify source files unless the user asks to address findings.
