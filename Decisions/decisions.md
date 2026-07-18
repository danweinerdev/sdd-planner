---
title: "Decision Ledger"
type: decision-log
status: active
created: 2026-07-18
updated: 2026-07-18
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
---

# Decision Ledger

Machine-readable record of decided truths. The frontmatter `decisions[]` array is canonical.
