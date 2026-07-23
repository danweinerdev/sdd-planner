# Completion Evidence

Prospective `verification` says how work will be judged. Retrospective
completion evidence records what actually ran and what it proved. A task,
phase, or plan may not transition to `complete` until its required evidence
section is populated and passes the rules below (D-0005).

## Required sections

- Every task body has `### Completion Evidence` within its `## <task-id>`
  section.
- Every phase document has `## Phase Completion Evidence`.
- Every plan README has `## Plan Completion Evidence`.

Incomplete work starts with the literal line `Pending — not complete.` in its
evidence section. The evidence may be populated while status is still
non-complete so it can be validated before the status transition. A `complete`
status and a pending or absent evidence section are contradictory states.

## Task evidence

Before setting a task to `complete`, replace the pending marker with:

```markdown
### Completion Evidence

- Verified: YYYY-MM-DD
- Repository: `<repository root>`
- VCS: `git | git-worktree | perforce | none`
- Revision / checkpoint: `<exact tested native SCM revision/checkpoint>`, `<Git base>-dirty`, `<Perforce have digest>`, or `none`
- Identity recheck: `<exact command/tool, timestamp, and matching revision/checkpoint/digest>`

<!-- Fallback identity only: add Evidence exclusions, Governing intent,
Ignored inputs, Directory inputs, and Content snapshot as defined below. -->

| Command | Working directory | Result | Observable evidence |
|---|---|---|---|
| `<exact command>` | `<path>` | PASS (`exit 0`) | `<specific output or behavior observed>` |

| Tool / inspection | Context | Result | Observable evidence |
|---|---|---|---|
| `<tool and version, or exact non-command procedure>` | `<paths/environment>` | PASS | `<specific observation>` |
```

Every completed task also includes these exact review-evidence labels before
its tables:

```markdown
- Focused review: `git show <full40>` or `git diff <full40>..<full40>`; complete task diff reviewed for correctness, scope, tests, maintainability, and task boundary
- Reviewed candidate / final: `<exact Revision / checkpoint identity>`
- Review result: PASS/Aligned
```

Rules:

1. Record the exact command, not “tests passed” or a paraphrased tool name.
2. Record the working directory and exit status for every command.
3. Record the observable result that satisfies the task's prospective
   `verification`; test counts alone are insufficient when named behaviors were
   required.
4. Record the tested source identity using the canonical procedure below. This
   is the focused native SCM revision/checkpoint, not a mutable working state or
   later lifecycle record. A changed-path list, ordinary text patch, or revision
   without the identity recheck is not reproducible evidence.
5. Name non-command tools and procedures precisely, including version when it
   affects reproducibility, plus the inspected paths/environment and observed
   result.
6. Remove an unused table only when that evidence class does not apply. At
   least one command or tool/inspection row is required. When behavior cannot
   be command-verified, state why and provide the exact non-command evidence.
7. A final required check that failed means the task is not complete. Preserve
   failure output verbatim in the session report or linked durable artifact;
   never rewrite failure as passing evidence.
8. The focused-review record is retrospective evidence of the **complete task
     diff**, not a reference to a later phase gate. For a clean Git, its command
     is exactly `git show <full task commit>` for final-commit review or `git
     diff <full base>..<full task commit>` for range review, before the required
     semicolon statement. For a clean Git
    task, `Reviewed candidate / final` is exactly the full task commit or
    `diff: <full40>..<full40>`; both commits must exist in the target repository,
    range endpoints must differ, the base must be the final task commit's direct
    first parent, and the range endpoint must exactly equal `Revision / checkpoint`.
     The exact backticked command uses that same full commit or range with no
     extra operands. Other SCMs
    record the exact native revision/checkpoint; no unsupported adapter may claim
    to validate an alternate diff identity. A task cannot become `complete`
    without this auditable `PASS/Aligned` result.

## Native SCM completion

Each plan task is one clean, complete, independently bisectable feature or
internal-capability slice (D-0014, D-0015):

1. Implement the task and its tests without mixing another feature slice.
2. Run the required verification and focused code review of the complete diff
   before finalizing the task revision/checkpoint.
3. Record the implementation as one scoped native SCM revision/checkpoint.
   Subtasks are steps within this boundary; they are not incomplete intermediate
   revisions. The recorded state must contain a complete behavior or coherent
   internal capability and keep the repository buildable/testable.
4. Confirm the native revision/checkpoint contains the exact tested bytes and
   record its full identity as `Revision / checkpoint`. It is the durable source
   identity; do not create a fallback capture merely because lifecycle evidence
   has not yet been written.
5. Populate completion evidence and lifecycle status, then record the complete
   planning artifact through its approved durable SCM lifecycle transport. The
   lifecycle record preserves complete task state while evidence continues to
   identify the tested implementation revision/checkpoint.

The completion transition is finalized only after both the implementation and
lifecycle identities exist. A planning root without approved durable lifecycle
transport may preserve a handoff state but the entity remains non-complete. No
transport may leave completed implementation dirty or replace an authorized
native revision/checkpoint with a content snapshot.

Durability validation dispatches by the detected **planning-root SCM**, not by
a universal Git assumption. The Git adapter below is currently the only
validated durable lifecycle adapter. Perforce and no-SCM planning roots have no
validated durable lifecycle adapter yet: they may retain handoff evidence, but
tasks, phases, and plans must remain non-complete rather than claiming durable
lifecycle completion.

### Git adapter: commit first

For Git repositories where commits are authorized, the native SCM revision in
step 3 is one scoped implementation commit (D-0011, D-0016, D-0017). Confirm the
implementation commit contains the exact tested bytes and record its full hash
as `Revision / checkpoint`. Then make a separate scoped lifecycle commit
containing only plan/evidence bookkeeping; this avoids a self-referential SHA.
Normal Git completion creates no snapshot manifest, content-object directory,
governing-intent projection, or `evidence/` folder.

## Fallback source identity

Dirty Git, Perforce, and no-VCS snapshots are compatibility mechanisms for
workspaces where a normal native revision/checkpoint is genuinely unavailable
or not authorized. They are not a reason to postpone an authorized Git commit.
Record the constraint or authorization that selected the fallback. A routine
in-progress Git task must stay non-complete rather than generating a snapshot
merely because evidence has not been written yet.

Fallback evidence adds these fields to the common task evidence:

- Fallback reason: `<specific VCS/authorization constraint selecting snapshot identity>`
- Evidence exclusions: `<exact repository-relative SDD artifact paths, or none>`
- Governing intent: `<sha256 digest> at <durable projection path>; inputs: <paths and decision ids>`
- Ignored inputs: `paths: <comma-separated repository-relative paths>; <digests/basis>`, or `none with <inspection basis>`
- Directory inputs: `paths: <comma-separated repository-relative paths>; <modes/basis>`, or `none with <inspection basis>`
- Content snapshot: `<sha256 digest> at <durable canonical manifest path>`

## Canonical source identity

Source identity covers every target repository touched by the task. Record a
separate revision/snapshot for each repository. The repository root, detected
VCS kind, and full implementation revision or fallback snapshot are part of the
identity; fallback identity also includes its governing-intent digest. A Git
bare repository is unsupported: operate in a worktree. Do not
improvise an identity for an unrecognized VCS.

For normal Git commit-backed evidence, the full tested implementation revision
and immediate commit/tree identity recheck are sufficient. The planning
artifact itself must be tracked and committed in its lifecycle commit. Later
feature commits do not make earlier task evidence stale: the recorded commit is
immutable retrospective identity, not an assertion that the current branch tip
still equals that historical task.

The remaining rules in this section apply to fallback snapshots. The only
permitted content-snapshot exclusions are exact repository-relative
paths of the governing phase document, plan README, phase debrief, canonical
snapshot manifest/content objects, and governing-intent projection object when
those files exist solely to record SDD evidence or lifecycle status. Evidence
capture paths must live under the planning root. The phase document and plan
README remain covered by the governing-intent digest below; excluding them does
not permit intent changes.
List every exclusion in the evidence. Source, tests, fixtures, generated
source, configuration, and any other implementation content may not be
excluded.

For fallback evidence, compute `Governing intent` over an explicit input set:
the plan README,
governing phase document, every governing spec/design consulted or cited by the
task, and every accepted decision consulted or cited by id. Resolve all
citations and record the sorted input references in evidence; an unresolved or
omitted governing input is nonconforming.

All projected artifacts must be UTF-8 with LF endings. Lifecycle fields must
use block-style YAML with each removable scalar on its own complete line and no
other node or comment on that line; flow-style or multiline lifecycle fields
are nonconforming until normalized. For plans/phases, remove only lines whose
parsed YAML path is top-level `updated`, top-level `status`,
`phases[*].status`, or `tasks[*].status`; replace each completion-evidence
section body with the exact line `Pending — not complete.\n`; and normalize
`[x]`/`[X]` to `[ ]` only in Subtasks and Acceptance Criteria. For governing
specs/designs, remove only standalone top-level `updated` and `status` lines.
For a decision input, project the exact YAML bytes of that one entry from its
`- id:` line through the byte before the next entry at the same indentation.
Retain every other byte.

The durable projection object is `sdd-intent-v2\n` followed, in encoded input-
reference order, by
`input\t<artifact-or-decision>\t<encoded-reference>\t<byte-count>\n<projected-bytes>`
for every input. `byte-count` is decimal and makes adjacent records
unambiguous. Paths/references use the encoding below. Store the exact projection
bytes at the recorded durable path and record their SHA-256. Recompute the
current projection during every pre-completion or pre-closure identity recheck;
a changed input set or digest invalidates prior verification. For an already-
closed historical entity, validate the durable projection bytes and digest but
do not compare them to artifacts legitimately revised by later work; report
later governing revisions separately as drift when applicable.

For a dirty identity, store a canonical snapshot manifest and content objects:

1. For Git, compare final worktree content to the fixed full base revision and
   enumerate every non-ignored untracked file. Require every staged path to
   match its worktree bytes/mode so hidden index content cannot later be
   committed untested. Treat a path absent from the base as `A` regardless of
   whether it is currently tracked. Include all differences except the
   permitted exclusions; do not select only paths believed relevant. Keep the
   recorded base fixed across evidence-only or implementation commits so the
   same tested bytes retain the same identity.
2. The manifest is UTF-8/ASCII with LF endings and a final LF. Its first two
   lines are `sdd-dirty-snapshot-v1` and `base\t<full-revision>`. Then emit one
   `exclude\t<path>` line per exclusion, one
   `directory\t<mode>\t<path>` line per captured directory, and one
   `entry\t<state>\t<mode>\t<size>\t<sha256>\t<path>` line per changed object.
   Emit those groups in that order and sort each by encoded path. Capture every
   empty directory and every directory whose existence or permissions affect
   verification or delivery; list them under `Directory inputs`. States are
   `A`, `M`, `D`, and `T`. Modes are lowercase fixed-width six-digit octal POSIX
   `st_mode & 0177777`, including type bits; use the final mode, byte size, and
   SHA-256 of raw content. Deletion uses mode `000000`, size `0`, and digest
   `-`. Reject identity capture on a platform that cannot report equivalent
   POSIX mode semantics.
3. Encode path bytes using ASCII letters, digits, `.`, `_`, `-`, and `/`
   literally and every other byte as uppercase `%HH`. Capture regular-file
   bytes exactly and symlink target bytes as content. A dirty submodule or
   nested repository requires its own snapshot and an evidence row naming its
   digest; the parent gitlink alone is insufficient.
4. Store every non-deletion content object at
   `<manifest-path>.contents/<sha256>` with exactly the hashed bytes. SHA-256 of
   the exact manifest bytes is the recorded content-snapshot digest.
5. A durable fallback path is either a VCS-tracked artifact committed with the SDD
   evidence or an immutable, content-addressed artifact URI with recorded
   retention. Because the base stays fixed and evidence paths are explicit
   exclusions, committing only fallback evidence files does not alter
   the tested content identity; changing any implementation byte does. A
   mutable temporary file is not durable.

Git ignore rules do not prove irrelevance. Include every ignored file read,
executed, or produced by verification, used as configuration/input, or shipped
as part of the deliverable as an `A`/`M` manifest entry and content object.
Include every ignored directory with relevant existence/mode as a directory
entry. Record each included ignored path under `Ignored inputs` and every
captured directory under `Directory inputs`. For omitted ignored paths or
directories, record the exact inspection/tool basis establishing that they
cannot affect verification or the deliverable; an unsupported blanket
“ignored” claim is nonconforming.

For Perforce and no-VCS workspaces, use this complete
`sdd-content-snapshot-v1` grammar instead of the Git delta manifest:

1. Snapshot every directory, regular file, and symlink recursively under the
   target root except permitted exclusions. Include empty directories and
   directory modes. Reject unsupported special files.
2. Emit these LF-terminated sections in order: `sdd-content-snapshot-v1`;
   `vcs\tperforce` or `vcs\tnone`; one `base\t<value>` line; sorted
   `exclude\t<encoded-path>` lines; sorted Perforce `have` lines when
   applicable; then sorted `entry` lines. The file ends with LF.
3. For Perforce, each have line is
   `have\t<encoded-depot-path>#<revision>\t<encoded-local-path>`. `base` is
   SHA-256 of the exact concatenated have-line bytes. Include the complete
   client mapping, including mapped files locally deleted. For no VCS, use
   `base\tnone` and no have lines.
4. Each entry is
   `entry\t<state>\t<type>\t<mode>\t<size>\t<sha256>\t<encoded-path>`.
   State is `P` for present or `D` for a locally deleted Perforce mapping. Type
   is `d`, `f`, or `l` for directory, regular file, or symlink. Mode is lowercase
   fixed-width six-digit octal POSIX `st_mode & 0177777`, including type bits;
   reject capture when equivalent POSIX mode semantics are unavailable. Present
   directories use size `0` and digest `-`; deleted entries use type `-`, mode
   `000000`, size `0`, and digest `-`; files hash raw bytes; symlinks hash raw
   target bytes. Entry sorting is by encoded path, then state and type.
5. Store every present file/symlink object at
   `<manifest-path>.contents/<sha256>`. For Perforce, include mapped, opened,
   reconciled, and local content. SHA-256 of the exact full manifest bytes is
   the recorded source identity.

This full snapshot is required even when Perforce has no pending edits or the
workspace has no VCS. Files or directories outside the target root that affect
verification must be listed as environment/input artifacts with exact paths,
content digests, and durable captures.

Capture fallback identity immediately after the recorded verification commands.
After writing evidence, recompute it with the same base and exclusions
immediately before each task/phase/plan status transition. Record the exact
recheck command or tool, timestamp, and matching revision/digest. Any
non-excluded difference from the tested identity makes the evidence stale and
forbids completion or closure.

## Phase evidence

Before setting a phase to `complete`, replace `Pending — not complete.` under
`## Phase Completion Evidence` with:

- verification date and canonical source identity under the task-evidence
  rules, including the tested implementation revision for normal Git or durable
  snapshot capture when fallback identity is required;
- the VCS kind and successful identity recheck, plus exact exclusions,
  governing-intent digest, and ignored/directory-input inventories only for a
  fallback snapshot;
- a rollup of every task id that repeats its populated `### Completion
  Evidence` section verbatim under `### Task <id> Evidence Rollup`;
- `Final aligned review`: `<persisted review artifact path>; frozen:
  <revision/range>` for a run of all four `sdd-code-review` lanes against the
  concrete phase state; its verdict must be `Aligned` and it must be the last
  material code state reviewed;
- exact phase-level commands/tools and results when the phase acceptance
  criteria require integration or aggregate checks; and
- either those aggregate checks or an explicit statement that no additional
  phase-level check applies, with the reason task evidence fully covers every
  phase acceptance criterion.

All phase acceptance-criteria checkboxes and tasks must be complete first. Every
required phase-level check must pass. A `Needs changes` or `Blocked` phase-gate
review forbids phase completion. Every review-driven material fix receives a
new planned task id and is implemented as a complete reviewable task revision,
even when it is small, then requires a fresh frozen four-lane review.
Any material code change after review — behavior, public contract, architecture,
security, concurrency, persistence, error handling, acceptance coverage, or
meaningful test logic — invalidates that review. Repeat until `Aligned` and
materially unchanged.

## Plan evidence

Before setting a plan to `complete`, replace `Pending — not complete.` under
`## Plan Completion Evidence` with:

- verification date and canonical source identity under the task-evidence
  rules, including the final tested implementation revision for normal Git or
  durable snapshot capture when fallback identity is required;
- the VCS kind and successful identity recheck, plus exact exclusions,
  governing-intent digest, and ignored/directory-input inventories only for a
  fallback snapshot;
- a rollup for every phase and task that repeats the exact commands/tools,
  context, results, and observable evidence from their completion sections;
  use one `### Phase <id> Evidence Rollup` and one
  `### Task <id> Evidence Rollup` block per child; links may supplement the
  rollup but references alone are insufficient;
- exact plan-level end-to-end/release commands or tools and results when the
  plan's deliverable requires them; and
- either those final checks or an explicit statement that no additional
  plan-level check applies, with the reason phase evidence fully proves the
  plan deliverable.

Every phase must be complete first. Every required plan-level check must pass;
a failed or unrun final check forbids plan completion.

## Legacy completed artifacts

Artifacts already marked `complete` without the required section are legacy
evidence gaps. Do not fabricate evidence, silently downgrade status, or infer
commands from checked boxes. `sdd-validate` reports them. They become conforming
only when verification is rerun or a contemporaneous durable record (for
example, CI output tied to a revision) supplies every required field.
