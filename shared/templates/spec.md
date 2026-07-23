---
title: "{{TITLE}}"
type: spec
status: draft
created: {{DATE}}
updated: {{DATE}}
tags: []
related: []
---

# {{TITLE}}

<!-- sdd-validate format contract:
- Store this document as UTF-8 with LF line endings and keep the YAML
  frontmatter as a mapping between standalone `---` delimiters.
- Keep `title`, `type`, `status`, `created`, `updated`, `tags`, and `related`;
  dates use `YYYY-MM-DD` and status is one of `draft`, `review`, `approved`,
  `implemented`, or `superseded`.
- Keep every H2 heading supplied by this template with exactly the shown text.
- Keep `tags` and `related` as YAML lists. Each `related` value must be a
  nonempty planning-root-relative artifact path that resolves; do not use an
  absolute path, backslashes, `.` segments, or `..` segments.
- Define at least one item in each identifier family using these exact parser
  forms: `- **FR-NN**: ...`, `- **NFR-NN**: ...`, and
  `- [ ] **AC-NN**: ...` (checked acceptance criteria may use `[x]` or `[X]`).
  Use at least two digits and keep IDs unique in this spec. IDs are append-only;
  when a Git HEAD version exists, the validator rejects removal. Preserve a
  retired ID with `removed — see <reason/citation>` or a struck-through line.
- Any D-NNNN citation must resolve in the applicable decision ledger; a live
  spec must not cite a rejected or superseded decision.
-->

## Overview
Brief description of the feature and its purpose.

## Goals
-

## Non-Goals
-

## Requirements
<!-- External contracts (third-party APIs, protocols, wire formats, other teams' interfaces): pin the source — link the authoritative doc and record its version and as-of date. -->

### Functional Requirements
- **FR-01**:

### Non-Functional Requirements
- **NFR-01**:

## User Stories
- As a [user], I want to [action] so that [benefit].

## Acceptance Criteria
- [ ] **AC-01**:

## Constraints
-

## Dependencies
-

## Open Questions
<!-- Before `approved`/`implemented`, resolve every question or use the exact
form `- <question> — **non-blocking** — <rationale>`. The marker without a
rationale is invalid. Use `- None.` when no questions remain. -->
- None.
