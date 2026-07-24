---
title: "Decision Ledger"
type: decision-log
status: active
created: 2026-07-18
updated: 2026-07-23
tags: [decisions]
related: []
decisions:
  - id: D-0001
    kind: decision
    status: accepted
    date: 2026-07-18
    decided_by: user
    statement: "Bundled shared resources must be resolved from the plugin installation root derived from the loaded skill or the runtime's standard skill locations, never relative to the working directory."
    rejected: ["Resolve shared paths relative to the working directory"]
    rationale: "Skills may be loaded from different host-specific locations, including OpenCode Agent Skills roots and Codex plugin caches, while the shared directory remains a sibling of the plugin's skills directory."
    confirmation: "Every SKILL.md bootstraps the plugin root before opening shared resources, and shared/agent-runtime.md lists and validates the supported discovery locations."
    scope: [skills, shared/agent-runtime.md]
    tags: [plugin-resources, path-resolution, runtime-neutral]
  - id: D-0002
    kind: decision
    status: accepted
    date: 2026-07-18
    decided_by: user
    statement: "SDD workflows must read the installed plugin, skills, and shared resources in place and must never copy or symlink bundled plugin material into a working directory, target repository, or planning root."
    rejected: ["Copy plugin resources into the workspace as a discovery or access workaround"]
    rationale: "Plugin material has host-specific installed locations and is workflow input, while the workspace should contain generated SDD outputs rather than duplicated runtime resources."
    confirmation: "Every SKILL.md states the resource boundary, shared/agent-runtime.md defines read-in-place behavior and failure handling, and setup forbids plugin-resource copies and symlinks."
    scope: [skills, shared/agent-runtime.md, shared/path-resolution.md]
    tags: [plugin-resources, workspace-boundary, read-in-place]
  - id: D-0003
    kind: decision
    status: superseded
    superseded_by: D-0016
    date: 2026-07-18
    decided_by: user
    statement: "Completed repository changes must be recorded in clean, scoped commits."
    rejected: ["Leave completed changes uncommitted", "Mix unrelated changes in one commit"]
    rationale: "Clean commits preserve reviewability and make completed work easy to trace or revert."
    confirmation: "At completion, inspect status and diff, commit only intended files with a repository-style message, and confirm the worktree is clean."
    scope: []
    tags: [git, commits, workflow]
  - id: D-0004
    kind: decision
    status: accepted
    date: 2026-07-21
    decided_by: user
    statement: "Every public sdd-planner skill name and installation directory uses the sdd- prefix, with no unprefixed compatibility aliases."
    rejected: ["Keep generic unprefixed skill names", "Use the longer sdd-planner- prefix"]
    rationale: "The sdd- prefix identifies ownership and prevents collisions in global skill discovery while remaining concise."
    confirmation: "Every skills/* directory and SKILL.md name starts with sdd-, and installed ~/.agents/skills links expose no legacy short-form sdd-planner names."
    scope: [skills, README.md]
    tags: [skill-names, namespace, installation]
  - id: D-0005
    kind: decision
    status: accepted
    date: 2026-07-21
    decided_by: user
    statement: "An SDD task, phase, or plan may not be marked complete until its artifact contains a populated completion-evidence section recording exactly what commands, tests, tools, or inspections ran and the observed results."
    rejected: ["Treat prospective verification criteria or checked subtasks as proof of completion", "Keep completion evidence only in conversation"]
    rationale: "Durable retrospective evidence makes completion auditable and gives execution trackers a concrete basis for closure instead of trusting status alone."
    confirmation: "shared/completion-evidence.md defines the required sections; lifecycle skills write and validate them before complete transitions; sdd-validate rejects missing, pending, stale, or failing evidence on complete entities."
    scope: [README.md, shared/completion-evidence.md, shared/frontmatter-schema.md, shared/templates/plan-readme.md, shared/templates/plan-phase.md, shared/agent-prompts/plan-reviewer.md, skills/sdd-plan, skills/sdd-implement, skills/sdd-debrief, skills/sdd-validate, skills/sdd-code-review]
    tags: [completion, verification, evidence, lifecycle]
  - id: D-0006
    kind: decision
    status: accepted
    date: 2026-07-21
    decided_by: user
    statement: "The sdd-planner public surface is a compact lifecycle core: diagram, excavate, retro, and simplify are removed; excavation becomes a research mode; broad tend is replaced by read-only deterministic sdd-validate."
    rejected: ["Keep all peripheral workflow skills in the core plugin", "Remove artifact validation together with tend"]
    rationale: "A smaller public surface reduces overlap and selection ambiguity while preserving the integrity checks required for status, evidence, dependency, identifier, and decision correctness."
    confirmation: "The manifest skills directory exposes exactly the documented core; removed skill paths and symlinks are absent; sdd-validate is read-only and runs the deterministic integrity checks."
    scope: [README.md, .codex-plugin/plugin.json, skills, shared/frontmatter-schema.md, shared/path-resolution.md, shared/templates/agents-md-full.md]
    tags: [skill-surface, compact-core, validation]
  - id: D-0007
    kind: decision
    status: accepted
    date: 2026-07-21
    decided_by: user
    statement: "Deterministic sdd-validate checks run through a versioned Python script using PyYAML; AI validation is reserved for semantic judgments that the script cannot establish."
    rejected: ["Perform every validation check by reading artifacts only in AI context", "Implement a partial YAML parser instead of using PyYAML"]
    rationale: "A scripted validator makes structural, reference, graph, and evidence-shape checks reproducible while retaining model judgment for whether content and evidence are semantically sufficient."
    confirmation: "The sdd-validate skill invokes the bundled validator first, its dependency on PyYAML is declared, and automated fixtures cover valid and invalid artifact graphs."
    scope: [skills/sdd-validate, scripts, tests]
    tags: [validation, python, pyyaml, deterministic-checks]
  - id: D-0008
    kind: decision
    status: accepted
    date: 2026-07-22
    decided_by: user
    statement: "SDD code-review lanes expose stable runtime-neutral dispatch identifiers that runtime adapters may map to named agents and models without making sdd-planner depend on those agents, models, or a delegation API."
    rejected: ["Embed OpenCode agent or model names in sdd-code-review", "Leave code-review lane dispatch labels implicit and unstable"]
    rationale: "Stable semantic identifiers preserve portable SDD workflows while allowing capable runtimes to select cost- and capability-appropriate workers deterministically."
    confirmation: "sdd-code-review and shared/review-lanes.md define the same exact lens-to-identifier mapping; tests enforce that mapping, runtime-neutral identifier text, and fresh-context/Mixed fallback language."
    scope: [skills/sdd-code-review, shared/review-lanes.md, shared/agent-runtime.md, README.md]
    tags: [code-review, dispatch, collaboration, runtime-neutral]
  - id: D-0009
    kind: decision
    status: accepted
    date: 2026-07-23
    decided_by: user-approved
    statement: "SDD code implementation dispatches use the stable runtime-neutral identifier implement_task, which runtime adapters may map to a dedicated implementer role with independently configurable model and effort while bounded-editor remains for mechanical edits."
    rejected: ["Route semantic code implementation through bounded-editor", "Embed OpenCode agent names or model identifiers in sdd-planner or sdd-beads"]
    rationale: "Separating semantic implementation from mechanical editing allows stronger reasoning for code changes without coupling portable SDD workflows to a runtime or overspending on simple text edits."
    confirmation: "sdd-implement emits implement_task without naming a runtime agent or model; runtime-adapter tests map it to implementer; model profile tests cover explicit selection and reasoner fallback."
    scope: [skills/sdd-implement, shared/agent-runtime.md, README.md]
    tags: [implementation, dispatch, collaboration, runtime-neutral, model-routing]
  - id: D-0010
    kind: decision
    status: accepted
    date: 2026-07-23
    decided_by: user
    statement: "Decision-ledger operations use a bundled deterministic validator for format and every safely machine-checkable invariant, while semantic collision judgment remains outside the script."
    rejected: ["Rely only on model inspection to validate decision-ledger structure", "Treat semantic contradiction judgments as deterministic"]
    rationale: "A focused validator catches malformed or inconsistent ledgers reproducibly before and after writes without pretending that differently worded decisions can be reconciled mechanically."
    confirmation: "The decision-log convention and both decision-writing skills invoke the bundled validator, and automated fixtures cover valid and invalid ledger states."
    scope: [shared/decision-log.md, skills/sdd-decide, skills/sdd-decision-log, scripts, tests]
    tags: [decision-log, validation, python, pyyaml, deterministic-checks]
  - id: D-0011
    kind: decision
    status: superseded
    superseded_by: D-0018
    date: 2026-07-23
    decided_by: user
    statement: "In commit-capable Git workflows, SDD implementation completes each focused task with a scoped implementation commit before recording completion evidence; the evidence records that tested commit, and content snapshots are fallback identity mechanisms rather than substitutes for normal feature commits."
    rejected: ["Keep completed Git implementation dirty while collecting evidence", "Create dirty-worktree snapshot folders merely because lifecycle evidence has not yet been written", "Mix implementation and later evidence bookkeeping into an untraceable working-tree batch"]
    rationale: "Commit-first execution preserves reviewable feature history and lets ordinary completion evidence identify an immutable tested revision without copying changed implementation files into an evidence folder. A later scoped lifecycle commit avoids self-referential commit identities."
    confirmation: "sdd-implement requires the implementation commit before final verification and evidence capture when commits are authorized; completion-evidence documents the implementation-revision plus lifecycle-commit model and reserves snapshots for genuine fallback cases; tests reject the old evidence-first optional-commit wording."
    scope: [README.md, shared/completion-evidence.md, shared/templates/plan-readme.md, shared/templates/plan-phase.md, skills/sdd-implement, skills/sdd-validate, scripts/sdd_validate.py, tests]
    tags: [git, commits, workflow, completion, evidence, snapshots]
  - id: D-0012
    kind: decision
    status: superseded
    superseded_by: D-0017
    date: 2026-07-23
    decided_by: user
    statement: "Implementation plans must break work into task-sized feature slices whose completed implementation commits are clean, complete, and independently bisectable; subtasks are steps within that commit boundary, not separate incomplete commits."
    rejected: ["Plan tasks around arbitrary file or layer boundaries that leave the repository behaviorally incomplete", "Commit each mechanical subtask independently when it does not form a complete feature slice", "Accumulate multiple complete feature slices into one broad implementation commit"]
    rationale: "Making plan tasks correspond to complete behavioral slices gives implementation an explicit commit boundary, keeps every completed commit testable, and preserves useful git bisect and revert behavior."
    confirmation: "sdd-plan defines task boundaries as complete bisectable feature slices, plan review checks each proposed task as an independent commit boundary, sdd-implement commits one such task at a time, and templates expose the rule to generated plans."
    scope: [README.md, shared/frontmatter-schema.md, shared/agent-prompts/plan-reviewer.md, shared/templates/plan-phase.md, skills/sdd-plan, skills/sdd-implement, tests]
    tags: [planning, tasks, features, git, commits, bisectability, workflow]
  - id: D-0013
    kind: decision
    status: accepted
    date: 2026-07-23
    decided_by: user
    statement: "A scoped SDD validation resolves the selected artifact set and follows transitive explicit related links, so plan validation covers plan-owned artifacts and their governing related-artifact graph while excluding unrelated artifact findings."
    rejected: ["Keep scoped validation limited to path-prefix filtering", "Maintain a separate temporary graph-validator wrapper", "Claim unparsed files were validated merely because a related path exists"]
    rationale: "Graph-aware scope makes focused validation match the SDD intent graph without duplicating the validator or hiding the distinction between discoverable validated artifacts and unresolved references."
    confirmation: "sdd_validate.py computes a transitive closure over discovered artifacts for --scope, preserves global operational and decision-ledger diagnostics, reports artifacts_in_scope, and tests plan-owned, transitive-related, unrelated, unresolved, and severity behavior."
    scope: [scripts/sdd_validate.py, skills/sdd-validate, tests]
    tags: [validation, scope, graph, related-artifacts, deterministic-checks]
  - id: D-0014
    kind: decision
    status: accepted
    date: 2026-07-23
    decided_by: user
    statement: "SDD plans decompose implementation into cohesive, complete, independently bisectable task units that are code-reviewed and recorded in their complete state as native SCM revisions; phase completion requires a full multi-lane SDD code review, and material review-driven changes require another full multi-lane review until no material changes remain."
    rejected: ["Use partial or layer-only task boundaries", "Complete a phase without the full SDD review lanes", "Treat a materially changed post-review implementation as still reviewed"]
    rationale: "Complete task revisions preserve reviewability and bisectability, while an iterative phase gate validates the integrated result rather than only its individual pieces."
    confirmation: "Plan review checks task cohesion and completeness; implementation reviews and records each completed task through the detected SCM; phase completion remains blocked until all four SDD code-review lanes pass on the final materially unchanged phase diff."
    scope: [shared/review-lanes.md, shared/templates/plan-phase.md, shared/agent-prompts/plan-reviewer.md, skills/sdd-plan, skills/sdd-implement, skills/sdd-code-review, skills/sdd-validate, tests]
    tags: [planning, tasks, scm, commits, bisectability, code-review, phase-gate]
  - id: D-0015
    kind: decision
    status: accepted
    date: 2026-07-23
    decided_by: user
    statement: "The planner may split and reorder work into the smallest atomic task units needed to establish dependency order, provided every resulting task still lands a cohesive, complete, independently bisectable feature or internal capability."
    rejected: ["Preserve oversized tasks when smaller complete dependency-ordered units are available", "Create atomic tasks that leave a half-wired or broken intermediate state"]
    rationale: "Smaller complete units expose prerequisite order and reduce implementation risk without sacrificing green, reviewable revision boundaries."
    confirmation: "Plan creation and review explicitly test whether tasks should be split or reordered for dependency clarity and reject any resulting boundary that is incomplete, unbuildable, or not independently verifiable."
    scope: [shared/frontmatter-schema.md, shared/templates/plan-phase.md, shared/agent-prompts/plan-reviewer.md, skills/sdd-plan, skills/sdd-implement, tests]
    tags: [planning, decomposition, tasks, dependencies, atomicity, bisectability]
  - id: D-0016
    kind: decision
    status: accepted
    date: 2026-07-23
    decided_by: user
    statement: "Completed repository changes must be recorded as clean, scoped native SCM revisions or checkpoints; in Git this means commits, while other SCMs use their own durable revision primitive."
    rejected: ["Make Git commits a universal SDD requirement", "Leave completed changes in an unrecorded mutable workspace state", "Mix unrelated changes in one native SCM revision"]
    rationale: "SDD remains SCM-agnostic while preserving durable, reviewable, and reversible completed states through each repository's native source-control mechanism."
    confirmation: "Lifecycle skills detect the SCM, use its native durable revision/checkpoint, and keep Git commit instructions inside a clearly labeled Git adapter."
    scope: [README.md, shared/vcs-detection.md, shared/completion-evidence.md, skills/sdd-implement, skills/sdd-validate, tests]
    tags: [scm, revisions, commits, workflow, portability]
    supersedes: D-0003
  - id: D-0017
    kind: decision
    status: accepted
    date: 2026-07-23
    decided_by: user
    statement: "Implementation plans use the smallest dependency-ordered task units that each produce a cohesive, complete, independently bisectable native SCM revision or checkpoint; subtasks are mechanical steps within that complete boundary."
    rejected: ["Define every task as a Git commit regardless of SCM", "Create incomplete intermediate task revisions", "Combine independently complete dependency-ordered units into an oversized task"]
    rationale: "Native revision boundaries preserve SCM neutrality while small complete units make ordering explicit, reduce implementation risk, and keep every landed state reviewable and green."
    confirmation: "Planning and plan review split and reorder unfinished work where useful, reject incomplete boundaries, and describe Git commits only in Git-specific adapter guidance."
    scope: [README.md, shared/frontmatter-schema.md, shared/agent-prompts/plan-reviewer.md, shared/templates/plan-phase.md, skills/sdd-plan, skills/sdd-implement, tests]
    tags: [planning, tasks, scm, dependencies, atomicity, bisectability]
    supersedes: D-0012
  - id: D-0018
    kind: decision
    status: accepted
    date: 2026-07-23
    decided_by: user
    statement: "SDD completion evidence uses native SCM revisions or checkpoints as its sole durable source identity and records concise verification and review results; it never builds synthetic filesystem snapshots, content-object stores, custom intent hashes, retention proofs, or verbatim child-evidence rollups."
    rejected: ["Snapshot dirty worktrees into SDD evidence folders", "Build content-addressed source identity inside the planning system", "Duplicate task evidence verbatim into phase and plan evidence", "Use custom SHA-256 intent projections when native SCM revisions can identify reviewed artifacts"]
    rationale: "SCM owns source identity while SDD owns planning, verification, and review. Removing the parallel evidence storage system keeps completion auditable without reproducing source control or generating disproportionate artifacts."
    confirmation: "Completion contracts, templates, skills, and sdd_validate require native SCM identities and concise references only; snapshot/projection/IPFS helpers and fallback fields are absent; dirty or no-SCM work remains non-complete until a durable native checkpoint exists."
    scope: [README.md, shared/completion-evidence.md, shared/review-artifacts.md, shared/templates/plan-readme.md, shared/templates/plan-phase.md, shared/templates/review.md, skills/sdd-implement, skills/sdd-code-review, skills/sdd-debrief, skills/sdd-validate, scripts/sdd_validate.py, tests]
    tags: [completion, evidence, scm, snapshots, hashes, rollups, simplification]
    supersedes: D-0011
---

# Decision Ledger

Machine-readable record of decided truths. The frontmatter `decisions[]` array is canonical.
