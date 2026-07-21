---
name: sdd-simplify
description: "Simplify implemented code while preserving behavior. Use after implementation when asked to reduce complexity, remove duplication, or improve maintainability with verification."
---

# Code Simplification

## Resources

Before opening `shared/...`, follow symlinks in this loaded file's path, then derive `<plugin-root>` from `<plugin-root>/skills/<name>/SKILL.md`; fallback search roots are repository/user `.agents/` (including `$HOME/.agents/plugins/*/`), Codex `${CODEX_HOME:-$HOME/.codex}/plugins/cache/*/*/*/`, and runtime-configured skill roots. Accept only a root containing this skill, `shared/agent-runtime.md`, and the matching plugin manifest; never use the working directory. Then read `<plugin-root>/shared/agent-runtime.md`, `<plugin-root>/shared/path-resolution.md`, and `<plugin-root>/shared/vcs-detection.md`.

**Resource boundary:** Read the plugin, all `SKILL.md` files, and `shared/` resources in place. Never copy or symlink them into the working directory, target repository, or planning root. Only generated SDD outputs may be materialized from bundled resources.

## Process

1. Identify target files or a completed plan phase. Read the code, tests, callers, and relevant recent diff.
2. Produce a short list of validated simplifications. For each, state the behavior preserved, files affected, risk, and verification command.
3. Present behavior-affecting changes for user approval. Safe, local refactors may proceed autonomously when the request authorizes implementation.
4. Apply focused changes and run the project's relevant tests, type checks, linters, or build commands. If verification fails, fix the change or restore the affected change before reporting failure.
5. If linked to a plan, record completed simplification work in its debrief or phase only after verification.

## Constraints

- Do not rewrite working code wholesale.
- Do not call a change verified without command output.
- Prefer existing project conventions over abstract cleanup preferences.
- Do not rely on runtime-specific agent names or plugin-defined worker roles.
