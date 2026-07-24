from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN_ROOT / "scripts" / "sdd_validate.py"
SPEC = importlib.util.spec_from_file_location("sdd_validate", SCRIPT)
assert SPEC and SPEC.loader
sdd_validate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sdd_validate
SPEC.loader.exec_module(sdd_validate)


def write(root: Path, relative: str, contents: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")


def spec_document() -> str:
    return """
        ---
        title: Feature
        type: spec
        status: approved
        created: 2026-07-21
        updated: 2026-07-21
        tags: [feature]
        related: []
        ---
        # Feature
        ## Overview
        Feature overview.
        ## Goals
        - Goal.
        ## Non-Goals
        - Non-goal.
        ## Requirements
        ### Functional Requirements
        - **FR-01**: Do the thing.
        ### Non-Functional Requirements
        - **NFR-01**: Remain deterministic.
        ## User Stories
        - As a user, I can do the thing.
        ## Acceptance Criteria
        - [ ] **AC-01**: The thing works.
        ## Constraints
        - Constraint.
        ## Dependencies
        - None.
        ## Open Questions
        - None.
    """


def plan_document(phase_status: str = "planned", depends_on: str = "") -> str:
    dependency = f"    depends_on: [{depends_on}]\n" if depends_on else ""
    return f"""
        ---
        title: Feature Plan
        type: plan
        status: active
        created: 2026-07-21
        updated: 2026-07-21
        tags: [feature]
        related: [Specs/Feature]
        phases:
          - id: 1
            title: Build
            status: {phase_status}
            doc: 01-Build.md
        {dependency.rstrip()}
        ---
        # Feature Plan
        ## Overview
        Build the feature.
        ## Architecture
        One component.
        ## Key Decisions
        None.
        ## Dependencies
        None.
        ## Plan Completion Evidence
        Pending — not complete.
    """


def phase_document(task_status: str = "planned", depends_on: str = "") -> str:
    dependency = f'    depends_on: ["{depends_on}"]\n' if depends_on else ""
    return f"""
        ---
        title: Build
        type: phase
        plan: Feature
        phase: 1
        status: planned
        created: 2026-07-21
        updated: 2026-07-21
        deliverable: Feature implementation
        tasks:
          - id: "1.1"
            title: Implement
            status: {task_status}
            verification: "Run tests and satisfy FR-01, NFR-01, and AC-01"
        {dependency.rstrip()}
        ---
        # Phase 1: Build
        ## Overview
        Build it according to FR-01 and NFR-01.
        ## 1.1: Implement
        ### Subtasks
        - [ ] Implement it.
        ### Notes
        Follow AC-01.
        ### Completion Evidence
        Pending — not complete.
        ## Acceptance Criteria
        - [ ] AC-01
        ## Phase Completion Evidence
        Pending — not complete.
    """


class ValidatorTests(unittest.TestCase):
    def make_valid_tree(self, root: Path) -> None:
        write(root, "Specs/Feature/README.md", spec_document())
        write(root, "Plans/Feature/README.md", plan_document())
        write(root, "Plans/Feature/01-Build.md", phase_document())
        write(
            root,
            "Decisions/decisions.md",
            """
            ---
            title: Decision Ledger
            type: decision-log
            status: active
            created: 2026-07-21
            updated: 2026-07-21
            tags: [decisions]
            related: []
            decisions: []
            ---
            # Decision Ledger
            """,
        )

    def validate(self, root: Path) -> list[object]:
        return sdd_validate.Validator(root, root).run()

    def commit_all(self, root: Path) -> str:
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-m",
                "fixture",
            ],
            cwd=root,
            check=True,
            capture_output=True,
        )
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def complete_phase_and_plan(self, root: Path) -> tuple[str, str]:
        """Create a fully durable one-task phase and plan lifecycle fixture."""
        base = self.commit_all(root)
        (root / "implementation.txt").write_text("complete\n", encoding="utf-8")
        subprocess.run(["git", "add", "implementation.txt"], cwd=root, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "implement feature"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        checkpoint = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        task_evidence = f"""- Verified: 2026-07-24
- Repository: `{root}`
- VCS: `git`
- Revision / checkpoint: `{checkpoint}`
- Identity recheck: `git show {checkpoint}`, 2026-07-24T12:00:00Z, matched commit
- Focused review: `git show {checkpoint}`; complete task diff reviewed for correctness, scope, tests, maintainability, and task boundary
- Reviewed candidate / final: `{checkpoint}`
- Review result: PASS/Aligned

| Command | Working directory | Result | Observable evidence |
|---|---|---|---|
| `python3 -m unittest` | `{root}` | PASS (exit 0) | Task behavior passed. |"""
        phase_evidence = f"""- Verified: 2026-07-24
- Repository: `{root}`
- VCS: `git`
- Revision / checkpoint: `{checkpoint}`
- Identity recheck: `git show {checkpoint}`, 2026-07-24T12:00:00Z, matched commit
- Final aligned review: Plans/Feature/reviews/01-final.md; frozen: {base}..{checkpoint}

| Command | Working directory | Result | Observable evidence |
|---|---|---|---|
| `python3 -m unittest` | `{root}` | PASS (exit 0) | Aggregate phase checks passed after task verification. |

### Completed task identities
- `1.1`: `{checkpoint}`"""
        phase = phase_document(task_status="complete")
        phase = phase.replace("status: planned", "status: complete", 1)
        phase = phase.replace("- [ ] Implement it.", "- [x] Implement it.")
        phase = phase.replace("- [ ] AC-01", "- [x] AC-01")
        phase = phase.replace(
            "Pending — not complete.", task_evidence.replace("\n", "\n        "), 1
        )
        phase = phase.replace(
            "Pending — not complete.", phase_evidence.replace("\n", "\n        "), 1
        )
        write(root, "Plans/Feature/01-Build.md", phase)
        write(root, "Plans/Feature/README.md", plan_document(phase_status="complete"))
        review = f"""
            ---
            title: Final phase review
            type: review
            status: resolved
            created: 2026-07-24
            updated: 2026-07-24
            tags: [review]
            related: [Plans/Feature/01-Build.md]
            review_of: Plans/Feature/01-Build.md
            rev: {base}..{checkpoint}
            review_scope: phase
            frozen: true
            verdict: Aligned
            reviewed_planning_revision: {base}
            review_mode: independent
            lane_results:
              - lane: review_plan_drift
                result: PASS/Aligned
                reviewed_identity: {base}..{checkpoint}
                evidence: Phase checklist matched task completion evidence.
              - lane: review_quality
                result: PASS/Aligned
                reviewed_identity: {base}..{checkpoint}
                evidence: Implementation error paths were inspected.
              - lane: review_spec_compliance
                result: PASS/Aligned
                reviewed_identity: {base}..{checkpoint}
                evidence: AC-01 behavior matched the implementation diff.
              - lane: review_blind_spots
                result: PASS/Aligned
                reviewed_identity: {base}..{checkpoint}
                evidence: Empty input behavior was inspected.
            findings: []
            followups: []
            ---
            # Final phase review
            ## Findings
            ## Resolution Log
        """
        write(root, "Plans/Feature/reviews/01-final.md", review)
        subprocess.run(
            ["git", "add", "Plans/Feature/01-Build.md", "Plans/Feature/README.md", "Plans/Feature/reviews/01-final.md"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "complete phase lifecycle"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        plan_evidence = f"""- Verified: 2026-07-24
- Repository: `{root}`
- VCS: `git`
- Revision / checkpoint: `{checkpoint}`
- Identity recheck: `git show {checkpoint}`, 2026-07-24T12:00:00Z, matched commit

| Command | Working directory | Result | Observable evidence |
|---|---|---|---|
| `python3 -m unittest` | `{root}` | PASS (exit 0) | Aggregate plan checks passed after phase closure. |

### Completed phase identities
- `1`: `{checkpoint}`; review: `Plans/Feature/reviews/01-final.md`"""
        plan = plan_document(phase_status="complete").replace("status: active", "status: complete", 1)
        write(
            root,
            "Plans/Feature/README.md",
            plan.replace("Pending — not complete.", plan_evidence.replace("\n", "\n        ")),
        )
        subprocess.run(["git", "add", "Plans/Feature/README.md"], cwd=root, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "complete plan lifecycle"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        return base, checkpoint

    def test_valid_artifact_graph(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            self.assertEqual([], self.validate(root))

    def test_core_templates_state_the_validator_format_contract(self) -> None:
        templates = {
            kind: (PLUGIN_ROOT / "shared" / "templates" / filename).read_text(
                encoding="utf-8"
            )
            for kind, filename in {
                "spec": "spec.md",
                "design": "design.md",
                "plan": "plan-readme.md",
                "phase": "plan-phase.md",
            }.items()
        }

        for kind, headings in sdd_validate.REQUIRED_HEADINGS.items():
            if kind not in templates:
                continue
            for heading in headings:
                self.assertIn(f"## {heading}", templates[kind])
            for status in sdd_validate.STATUS[kind]:
                self.assertIn(f"`{status}`", templates[kind])
            for field in sdd_validate.COMMON_FIELDS:
                self.assertIn(f"{field}:", templates[kind])
            self.assertIn("sdd-validate format contract", templates[kind])
            self.assertNotIn("\r\n", templates[kind])

        for family, pattern in sdd_validate.DEFINITIONS.items():
            self.assertIsNotNone(pattern.search(templates["spec"]), family)
        self.assertIn("exact parser", templates["spec"])
        self.assertIn("collectively must cite every FR-NN and NFR-NN", templates["design"])

        plan = templates["plan"]
        self.assertIn("#   - id:", plan)
        for field in ("title", "status", "doc"):
            self.assertIn(f"#     {field}:", plan)
        self.assertRegex(plan, r"no unknown IDs,\s+self-dependencies, or cycles")

        phase = templates["phase"]
        for field in ("id", "title", "status", "verification"):
            self.assertIn(f"#   {field}:", phase)
        self.assertIn("`<phase>.<digits>`", phase)
        self.assertIn("exact H3 headings `Subtasks`,\n  `Notes`, and `Completion Evidence`", phase)

        for evidence_template in (plan, phase):
            for label in (
                "Verified",
                "Repository",
                "VCS",
                "Revision / checkpoint",
                "Identity recheck",
            ):
                self.assertIn(f"`{label}`", evidence_template)
            for removed in (
                "Evidence exclusions",
                "Governing intent",
                "Ignored inputs",
                "Directory inputs",
                "Fallback reason",
                "Content snapshot",
            ):
                self.assertNotIn(f"`{removed}`", evidence_template)
            self.assertIn(
                "`Command | Working directory | Result | Observable evidence`",
                evidence_template,
            )
            self.assertIn(
                "`Tool / inspection | Context | Result | Observable evidence`",
                evidence_template,
            )
            self.assertIn("`PASS (exit 0)`", evidence_template)
            self.assertIn("may be a validated integration merge", evidence_template)
            self.assertIn(
                "non-merge rule applies only to atomic task implementation evidence",
                evidence_template,
            )

    def test_validate_skill_retains_semantic_process_contract_with_native_scm_evidence(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "sdd-validate" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        for section in (
            "## Scope",
            "### Structure and frontmatter",
            "### Hierarchy, dependencies, and traceability",
            "### Review artifacts",
            "### Completion evidence",
            "### Decision ledger",
            "## Output",
        ):
            self.assertIn(section, skill)
        for requirement in (
            "cross-artifact semantic reconciliation",
            "Actively test the unhappy paths",
            "related` graph",
            "Review supersession links are bidirectional",
            "Complete parent entities contain no incomplete child entity",
            "files and checks inspected",
            "sole durable source identity",
            "Never use snapshots, content-object stores, custom intent hashes",
            "checkpoint identities, not child-evidence rollups",
        ):
            self.assertIn(requirement, skill)

    def test_plan_phase_docs_require_type_backlink_and_matching_title(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            phase = phase_document()
            phase = phase.replace("type: phase", "type: design", 1)
            phase = phase.replace("plan: Feature", "plan: Other", 1)
            phase = phase.replace("title: Build", "title: Other", 1)
            write(root, "Plans/Feature/01-Build.md", phase)
            codes = {item.code for item in self.validate(root)}
            self.assertTrue({"SDD150", "SDD151", "SDD152"}.issubset(codes))

    def test_every_phase_is_owned_once_by_its_physical_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            rogue = phase_document().replace("phase: 1", "phase: 9", 1)
            rogue = rogue.replace('id: "1.1"', 'id: "9.1"', 1)
            rogue = rogue.replace("## 1.1:", "## 9.1:", 1)
            write(root, "Plans/Other/09-Rogue.md", rogue)
            findings = [item for item in self.validate(root) if item.code == "SDD163"]
            self.assertEqual(1, len(findings))
            self.assertEqual("Plans/Other/09-Rogue.md", findings[0].path)

    def test_git_head_ids_are_append_only_but_retirement_is_retained(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            self.commit_all(root)

            spec = spec_document().replace("FR-01", "FR-02")
            write(root, "Specs/Feature/README.md", spec)
            plan = plan_document().replace("- id: 1", "- id: 2", 1)
            write(root, "Plans/Feature/README.md", plan)
            phase = phase_document().replace('id: "1.1"', 'id: "1.2"', 1)
            write(root, "Plans/Feature/01-Build.md", phase)
            codes = {item.code for item in self.validate(root)}
            self.assertTrue({"SDD154", "SDD155", "SDD156"}.issubset(codes))

            retired = spec_document().replace(
                "- **FR-01**: Do the thing.",
                "- **FR-01**: removed — see requirements retirement record",
            )
            write(root, "Specs/Feature/README.md", retired)
            self.assertNotIn(
                "SDD154",
                {item.code for item in self.validate(root) if item.path == "Specs/Feature/README.md"},
            )

    def test_append_only_ids_cover_deleted_paths_and_hidden_index_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            self.commit_all(root)
            spec_path = root / "Specs" / "Feature" / "README.md"

            staged = spec_document().replace("FR-01", "FR-02")
            spec_path.write_text(textwrap.dedent(staged).lstrip(), encoding="utf-8")
            subprocess.run(["git", "add", str(spec_path)], cwd=root, check=True)
            spec_path.write_text(textwrap.dedent(spec_document()).lstrip(), encoding="utf-8")
            findings = [item for item in self.validate(root) if item.code == "SDD154"]
            self.assertTrue(any("index" in item.message for item in findings))

            substituted = spec_document().replace("type: spec", "type: design", 1)
            spec_path.write_text(textwrap.dedent(substituted).lstrip(), encoding="utf-8")
            self.assertIn("SDD164", {item.code for item in self.validate(root)})

            subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=root, check=True, capture_output=True)
            spec_path.unlink()
            findings = [item for item in self.validate(root) if item.code == "SDD154"]
            self.assertTrue(any("worktree" in item.message for item in findings))

    def test_approved_open_questions_require_nonblocking_marker_and_rationale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            blocking = spec_document().replace("- None.", "- Which backend?")
            write(root, "Specs/Feature/README.md", blocking)
            self.assertIn("SDD153", {item.code for item in self.validate(root)})

            unexplained = spec_document().replace(
                "- None.", "- Which backend? — **non-blocking**"
            )
            write(root, "Specs/Feature/README.md", unexplained)
            self.assertIn("SDD153", {item.code for item in self.validate(root)})

            nonblocking = spec_document().replace(
                "- None.",
                "- Which backend? — **non-blocking** — Either backend satisfies FR-01.",
            )
            write(root, "Specs/Feature/README.md", nonblocking)
            self.assertNotIn("SDD153", {item.code for item in self.validate(root)})

            wrapped = spec_document().replace(
                "- None.",
                "- Which backend? — **non-blocking** — Either backend\n"
                "          satisfies FR-01.",
            )
            write(root, "Specs/Feature/README.md", wrapped)
            self.assertNotIn("SDD153", {item.code for item in self.validate(root)})

            mixed = spec_document().replace(
                "- None.", "Which backend owns writes?\n        - None."
            )
            write(root, "Specs/Feature/README.md", mixed)
            self.assertIn("SDD153", {item.code for item in self.validate(root)})

            draft = blocking.replace("status: approved", "status: draft", 1)
            write(root, "Specs/Feature/README.md", draft)
            self.assertNotIn("SDD153", {item.code for item in self.validate(root)})

    def test_complete_phase_requires_final_aligned_review_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            phase = phase_document(task_status="complete")
            phase = phase.replace("status: planned", "status: complete", 1)
            phase = phase.replace("- [ ] Implement it.", "- [x] Implement it.")
            phase = phase.replace("- [ ] AC-01", "- [x] AC-01")
            phase = phase.replace("Pending — not complete.", "Task proof.", 1)
            phase = phase.replace(
                "Pending — not complete.",
                "### Task 1.1 Evidence Rollup\n        Task proof.",
                1,
            )
            write(root, "Plans/Feature/01-Build.md", phase)
            write(root, "Plans/Feature/README.md", plan_document(phase_status="complete"))
            self.assertIn("SDD166", {item.code for item in self.validate(root)})

    def test_final_aligned_review_requires_exact_syntax_and_frozen_revision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            review = f"""
                ---
                title: Final phase review
                type: review
                status: resolved
                created: 2026-07-23
                updated: 2026-07-23
                tags: [review]
                related: [Plans/Feature/01-Build.md]
                review_of: Plans/Feature/01-Build.md
                rev: frozen-range-1
                review_scope: phase
                frozen: true
                verdict: Aligned
                reviewed_planning_revision: {'a' * 40}
                review_mode: independent
                lane_results:
                  - lane: review_plan_drift
                    result: PASS/Aligned
                    reviewed_identity: frozen-range-1
                    evidence: Phase checklist items match task completion evidence.
                  - lane: review_quality
                    result: PASS/Aligned
                    reviewed_identity: frozen-range-1
                    evidence: Changed implementation paths were inspected for error handling.
                  - lane: review_spec_compliance
                    result: PASS/Aligned
                    reviewed_identity: frozen-range-1
                    evidence: AC-01 behavior was compared against the implementation diff.
                  - lane: review_blind_spots
                    result: PASS/Aligned
                    reviewed_identity: frozen-range-1
                    evidence: Empty-input and failure branches were inspected in the diff.
                findings: []
                followups: []
                ---
                # Final phase review
                ## Findings
                ## Resolution Log
            """
            write(root, "Plans/Feature/reviews/01-final.md", review)
            phase = phase_document(task_status="complete")
            phase = phase.replace("status: planned", "status: complete", 1)
            phase = phase.replace("- [ ] Implement it.", "- [x] Implement it.")
            phase = phase.replace("- [ ] AC-01", "- [x] AC-01")
            phase = phase.replace("Pending — not complete.", "Task proof.", 1)
            phase = phase.replace(
                "Pending — not complete.",
                "- Final aligned review: Plans/Feature/reviews/01-final.md; frozen: frozen-range-1\n\n        ### Task 1.1 Evidence Rollup\n        Task proof.",
                1,
            )
            write(root, "Plans/Feature/01-Build.md", phase)
            codes = {item.code for item in self.validate(root)}
            self.assertFalse({"SDD166", "SDD167", "SDD168"} & codes)
            self.assertIn("SDD172", codes)

            mismatched = phase.replace("frozen: frozen-range-1", "frozen: another-range", 1)
            write(root, "Plans/Feature/01-Build.md", mismatched)
            self.assertIn("SDD168", {item.code for item in self.validate(root)})

            malformed = phase.replace("; frozen: frozen-range-1", ";frozen: frozen-range-1", 1)
            write(root, "Plans/Feature/01-Build.md", malformed)
            self.assertIn("SDD166", {item.code for item in self.validate(root)})

    def test_complete_task_requires_auditable_focused_review_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            revision = self.commit_all(root)
            body = f"""
                - Verified: 2026-07-23
                - Repository: `{root}`
                - VCS: `git`
                - Revision / checkpoint: `{revision}`
                - Identity recheck: `git diff-tree {revision}`, 2026-07-23T12:00:00Z, matched commit

                | Tool / inspection | Context | Result | Observable evidence |
                |---|---|---|---|
                | `inspection` | `repo` | PASS | Task behavior passed. |
            """
            validator = sdd_validate.Validator(root, root, "historical")
            validator._discover()
            artifact = validator.by_path["Plans/Feature/01-Build.md"]
            validator._evidence(
                artifact,
                "complete",
                "Task 1.1 Completion Evidence",
                1,
                textwrap.dedent(body),
            )
            self.assertIn("SDD169", {item.code for item in validator.out})

            validator.out.clear()
            reviewed = textwrap.dedent(body).replace(
                "- Identity recheck:",
                f"- Focused review: `git show {revision}`; complete task diff reviewed for correctness, scope, tests, maintainability, and task boundary\n"
                f"- Reviewed candidate / final: `{revision}`\n"
                "- Review result: PASS/Aligned\n"
                "- Identity recheck:",
            )
            validator._evidence(
                artifact,
                "complete",
                "Task 1.1 Completion Evidence",
                1,
                reviewed,
            )
            self.assertNotIn("SDD169", {item.code for item in validator.out})
            self.assertIn("SDD072", {item.code for item in validator.out})

            invalid_command = reviewed.replace(
                f"`git show {revision}`", "reviewed manually", 1
            )
            validator.out.clear()
            validator._evidence(
                artifact,
                "complete",
                "Task 1.1 Completion Evidence",
                1,
                invalid_command,
            )
            self.assertIn("SDD169", {item.code for item in validator.out})

            invalid_diff = reviewed.replace(
                f"- Reviewed candidate / final: `{revision}`",
                "- Reviewed candidate / final: `diff: x`",
                1,
            )
            validator.out.clear()
            validator._evidence(
                artifact,
                "complete",
                "Task 1.1 Completion Evidence",
                1,
                invalid_diff,
            )
            self.assertIn("SDD169", {item.code for item in validator.out})

    def test_clean_git_task_review_requires_direct_range_and_named_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            self.commit_all(root)
            (root / "intermediate.txt").write_text("base task state", encoding="utf-8")
            subprocess.run(["git", "add", "intermediate.txt"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "task base"], cwd=root, check=True, capture_output=True)
            parent = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
            (root / "implementation.txt").write_text("task complete", encoding="utf-8")
            subprocess.run(["git", "add", "implementation.txt"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "task final"], cwd=root, check=True, capture_output=True)
            final = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
            validator = sdd_validate.Validator(root, root, "historical")
            validator._discover()
            artifact = validator.by_path["Plans/Feature/01-Build.md"]
            reviewed = f"diff: {parent}..{final}"
            validator._valid_git_task_review_identity(artifact, "Task 1.1 Completion Evidence", f"git diff {parent}..{final}", reviewed, final, 1)
            self.assertNotIn("SDD169", {item.code for item in validator.out})

            validator.out.clear()
            validator._valid_git_task_review_identity(artifact, "Task 1.1 Completion Evidence", f"git show {final}", final, final, 1)
            self.assertNotIn("SDD169", {item.code for item in validator.out})

            for command in (
                f"git diff-tree {final}",
                f"printf {parent}..{final}",
                f"true {parent}..{final}",
                f"git diff {parent}..",
                f"git diff {final}..{parent}",
            ):
                validator.out.clear()
                validator._valid_git_task_review_identity(artifact, "Task 1.1 Completion Evidence", command, reviewed, final, 1)
                self.assertIn("SDD169", {item.code for item in validator.out}, command)

            validator.out.clear()
            validator._valid_git_task_review_identity(artifact, "Task 1.1 Completion Evidence", f"git diff-tree {final}", reviewed, final, 1)
            self.assertIn("SDD169", {item.code for item in validator.out})

            initial = subprocess.run(["git", "rev-parse", f"{parent}^"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
            validator.out.clear()
            validator._valid_git_task_review_identity(artifact, "Task 1.1 Completion Evidence", f"git diff {initial}..{final}", f"diff: {initial}..{final}", final, 1)
            self.assertIn("SDD169", {item.code for item in validator.out})

            validator.out.clear()
            validator._valid_git_task_review_identity(artifact, "Task 1.1 Completion Evidence", "git diff-tree", final, final, 1)
            self.assertIn("SDD169", {item.code for item in validator.out})

    def test_clean_git_task_review_rejects_merge_implementation_revision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            self.commit_all(root)
            main_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            subprocess.run(["git", "checkout", "-b", "side"], cwd=root, check=True, capture_output=True)
            (root / "side.txt").write_text("side", encoding="utf-8")
            subprocess.run(["git", "add", "side.txt"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "side"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "checkout", main_branch], cwd=root, check=True, capture_output=True)
            (root / "main.txt").write_text("main", encoding="utf-8")
            subprocess.run(["git", "add", "main.txt"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "main"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "merge", "--no-ff", "side", "-m", "merge task"], cwd=root, check=True, capture_output=True)
            merge = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
            validator = sdd_validate.Validator(root, root, "historical")
            validator._discover()
            artifact = validator.by_path["Plans/Feature/01-Build.md"]
            validator._valid_git_task_review_identity(
                artifact,
                "Task 1.1 Completion Evidence",
                f"git show {merge}",
                merge,
                merge,
                1,
            )
            diagnostics = [item for item in validator.out if item.code == "SDD169"]
            self.assertTrue(diagnostics)
            self.assertTrue(any("merge commit" in item.message for item in diagnostics))

    def test_git_phase_gate_requires_existing_exact_frozen_identity_and_checkpoint_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            base = self.commit_all(root)
            (root / "implementation.txt").write_text("complete", encoding="utf-8")
            subprocess.run(["git", "add", "implementation.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "implementation"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            checkpoint = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            body = f"""
                - VCS: `git`
                - Revision / checkpoint: `{checkpoint}`
            """
            validator = sdd_validate.Validator(root, root, "historical")
            validator._discover()
            phase = validator.by_path["Plans/Feature/01-Build.md"]

            validator._verify_phase_review_identity(
                phase, textwrap.dedent(body), "invented-review", 1
            )
            self.assertIn("SDD173", {item.code for item in validator.out})

            validator.out.clear()
            validator._verify_phase_review_identity(
                phase, textwrap.dedent(body), checkpoint, 1
            )
            self.assertIn("SDD173", {item.code for item in validator.out})

            validator.out.clear()
            missing = "a" * 40
            validator._verify_phase_review_identity(
                phase, textwrap.dedent(body), f"{base}..{missing}", 1
            )
            self.assertIn("SDD173", {item.code for item in validator.out})

            validator.out.clear()
            validator._verify_phase_review_identity(
                phase, textwrap.dedent(body), f"{base}..{base}", 1
            )
            self.assertIn("SDD173", {item.code for item in validator.out})

            validator.out.clear()
            validator._verify_phase_review_identity(
                phase, textwrap.dedent(body), f"{base}..{checkpoint}", 1
            )
            self.assertNotIn("SDD173", {item.code for item in validator.out})

    def test_git_phase_review_range_covers_every_completed_task_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            base = self.commit_all(root)
            (root / "task-one.txt").write_text("T1", encoding="utf-8")
            subprocess.run(["git", "add", "task-one.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "T1"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            task_one = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
            ).stdout.strip()
            (root / "task-two.txt").write_text("T2", encoding="utf-8")
            subprocess.run(["git", "add", "task-two.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "T2"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            task_two = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
            ).stdout.strip()
            body = f"""
                - VCS: `git`
                - Revision / checkpoint: `{task_two}`
            """
            validator = sdd_validate.Validator(root, root, "historical")
            validator._discover()
            phase = validator.by_path["Plans/Feature/01-Build.md"]
            task_identities = (("1.1", task_one), ("1.2", task_two))

            validator._verify_phase_review_identity(
                phase, textwrap.dedent(body), f"{task_one}..{task_two}", 1, task_identities
            )
            self.assertIn("SDD173", {item.code for item in validator.out})

            validator.out.clear()
            validator._verify_phase_review_identity(
                phase, textwrap.dedent(body), f"{base}..{task_two}", 1, task_identities
            )
            self.assertNotIn("SDD173", {item.code for item in validator.out})

    def test_git_phase_review_artifact_is_committed_and_unchanged_at_head(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            implementation_revision = self.commit_all(root)
            task_evidence = f"""
            - Verified: 2026-07-23
            - Repository: `{root}`
            - VCS: `git`
            - Revision / checkpoint: `{implementation_revision}`
            - Identity recheck: `git diff-tree {implementation_revision}`, 2026-07-23T12:00:00Z, matched commit
            - Focused review: `git show {implementation_revision}`; complete task diff reviewed for correctness, scope, tests, maintainability, and task boundary
            - Reviewed candidate / final: `{implementation_revision}`
            - Review result: PASS/Aligned

            | Command | Working directory | Result | Observable evidence |
            |---|---|---|---|
            | `python3 -m unittest` | `{root}` | PASS (`exit 0`) | Task behavior passed. |
            """
            task_evidence = textwrap.dedent(task_evidence).strip()
            indented_task = task_evidence.replace("\n", "\n        ")
            phase = textwrap.dedent(phase_document(task_status="complete"))
            phase = phase.replace("status: planned", "status: complete", 1)
            phase = phase.replace("- [ ] Implement it.", "- [x] Implement it.")
            phase = phase.replace("- [ ] AC-01", "- [x] AC-01")
            phase = phase.replace("Pending — not complete.", indented_task, 1)
            phase_evidence = f"""
            - Verified: 2026-07-23
            - Repository: `{root}`
            - VCS: `git`
            - Revision / checkpoint: `{implementation_revision}`
            - Identity recheck: `git diff-tree {implementation_revision}`, 2026-07-23T12:00:00Z, matched commit
            - Final aligned review: Plans/Feature/reviews/01-final.md; frozen: {implementation_revision}

            | Tool / inspection | Context | Result | Observable evidence |
            |---|---|---|---|
            | `phase inspection` | `{root}` | PASS | Phase behavior passed. |

            ### Task 1.1 Evidence Rollup
            {indented_task}
            """
            phase = phase.replace(
                "Pending — not complete.", textwrap.dedent(phase_evidence).strip(), 1
            )
            write(root, "Plans/Feature/01-Build.md", phase)
            write(root, "Plans/Feature/README.md", plan_document(phase_status="complete"))
            review = f"""
                ---
                title: Final phase review
                type: review
                status: resolved
                created: 2026-07-23
                updated: 2026-07-23
                tags: [review]
                related: [Plans/Feature/01-Build.md]
                review_of: Plans/Feature/01-Build.md
                rev: {implementation_revision}
                review_scope: phase
                frozen: true
                verdict: Aligned
                reviewed_planning_revision: {implementation_revision}
                review_mode: independent
                lane_results:
                  - lane: review_plan_drift
                    result: PASS/Aligned
                    reviewed_identity: {implementation_revision}
                    evidence: Phase checklist items match task completion evidence.
                  - lane: review_quality
                    result: PASS/Aligned
                    reviewed_identity: {implementation_revision}
                    evidence: Changed implementation paths were inspected for error handling.
                  - lane: review_spec_compliance
                    result: PASS/Aligned
                    reviewed_identity: {implementation_revision}
                    evidence: AC-01 behavior was compared against the implementation diff.
                  - lane: review_blind_spots
                    result: PASS/Aligned
                    reviewed_identity: {implementation_revision}
                    evidence: Empty-input and failure branches were inspected in the diff.
                findings: []
                followups: []
                ---
                # Final phase review
                ## Findings
                ## Resolution Log
            """
            write(root, "Plans/Feature/reviews/01-final.md", review)
            subprocess.run(
                ["git", "add", "Plans/Feature/01-Build.md", "Plans/Feature/README.md"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "Complete phase lifecycle"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            validator = sdd_validate.Validator(root, root, "current")
            validator._discover()
            validator._verify_git_phase_review_committed(
                validator.by_path["Plans/Feature/01-Build.md"],
                validator.by_path["Plans/Feature/reviews/01-final.md"],
                implementation_revision,
                1,
            )
            self.assertIn("SDD170", {item.code for item in validator.out})
            subprocess.run(["git", "add", "Plans/Feature/reviews/01-final.md"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "Commit final phase review"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            validator = sdd_validate.Validator(root, root, "current")
            validator._discover()
            validator._verify_git_phase_review_committed(
                validator.by_path["Plans/Feature/01-Build.md"],
                validator.by_path["Plans/Feature/reviews/01-final.md"],
                implementation_revision,
                1,
            )
            self.assertNotIn("SDD170", {item.code for item in validator.out})

            validator._verify_git_phase_post_review_state(
                validator.by_path["Plans/Feature/01-Build.md"],
                validator.by_path["Plans/Feature/reviews/01-final.md"],
                implementation_revision,
                1,
            )
            self.assertNotIn("SDD173", {item.code for item in validator.out})

            (root / "post-review-source.py").write_text("material change", encoding="utf-8")
            subprocess.run(["git", "add", "post-review-source.py"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "post-review source"], cwd=root, check=True, capture_output=True)
            validator.out.clear()
            validator._verify_git_phase_post_review_state(
                validator.by_path["Plans/Feature/01-Build.md"],
                validator.by_path["Plans/Feature/reviews/01-final.md"],
                implementation_revision,
                1,
            )
            self.assertIn("SDD173", {item.code for item in validator.out})
            historical = sdd_validate.Validator(root, root, "historical")
            historical._discover()
            historical._verify_git_phase_post_review_state(
                historical.by_path["Plans/Feature/01-Build.md"],
                historical.by_path["Plans/Feature/reviews/01-final.md"],
                implementation_revision,
                1,
            )
            self.assertNotIn("SDD173", {item.code for item in historical.out})

    def test_git_phase_post_review_state_rejects_dirty_target_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            endpoint = self.commit_all(root)
            validator = sdd_validate.Validator(root, root, "current")
            validator._discover()
            (root / "uncommitted-source.py").write_text("dirty", encoding="utf-8")
            phase = validator.by_path["Plans/Feature/01-Build.md"]
            validator._verify_git_phase_post_review_state(phase, phase, endpoint, 1)
            self.assertIn("SDD173", {item.code for item in validator.out})

            historical = sdd_validate.Validator(root, root, "historical")
            historical._discover()
            historical._verify_git_phase_post_review_state(
                historical.by_path["Plans/Feature/01-Build.md"],
                historical.by_path["Plans/Feature/01-Build.md"],
                endpoint,
                1,
            )
            self.assertNotIn("SDD173", {item.code for item in historical.out})

    def test_git_phase_post_review_state_rejects_dirty_ignored_submodule(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            source = Path(directory) / "source"
            source.mkdir()
            (source / "tracked.txt").write_text("clean", encoding="utf-8")
            subprocess.run(["git", "init"], cwd=source, check=True, capture_output=True)
            subprocess.run(["git", "add", "tracked.txt"], cwd=source, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "source"],
                cwd=source,
                check=True,
                capture_output=True,
            )
            self.make_valid_tree(root)
            self.commit_all(root)
            subprocess.run(
                ["git", "-c", "protocol.file.allow=always", "submodule", "add", str(source), "submodule"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-am", "add submodule"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            endpoint = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
            ).stdout.strip()
            subprocess.run(["git", "config", "submodule.submodule.ignore", "all"], cwd=root, check=True)
            (root / "submodule" / "tracked.txt").write_text("dirty", encoding="utf-8")
            validator = sdd_validate.Validator(root, root, "current")
            validator._discover()
            phase = validator.by_path["Plans/Feature/01-Build.md"]
            validator._verify_git_phase_post_review_state(phase, phase, endpoint, 1)
            self.assertIn("SDD173", {item.code for item in validator.out})

    def test_git_phase_post_review_state_rejects_reverted_source_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            endpoint = self.commit_all(root)
            (root / "post-review-source.py").write_text("changed\n", encoding="utf-8")
            subprocess.run(["git", "add", "post-review-source.py"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "post-review source"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "revert", "--no-edit", "HEAD"], cwd=root, check=True, capture_output=True)
            validator = sdd_validate.Validator(root, root, "current")
            validator._discover()
            phase = validator.by_path["Plans/Feature/01-Build.md"]
            validator._verify_git_phase_post_review_state(phase, phase, endpoint, 1)
            self.assertIn("SDD173", {item.code for item in validator.out})

    def test_git_phase_post_review_state_rejects_plan_and_phase_intent_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            endpoint = self.commit_all(root)
            phase_path = root / "Plans/Feature/01-Build.md"
            phase_path.write_text(
                phase_path.read_text(encoding="utf-8").replace(
                    "Build it according to FR-01 and NFR-01.", "Build a different feature."
                ),
                encoding="utf-8",
            )
            plan_path = root / "Plans/Feature/README.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "Build the feature.", "Build a different feature."
                ),
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "Plans/Feature/01-Build.md", "Plans/Feature/README.md"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "mutate reviewed intent"], cwd=root, check=True, capture_output=True)
            validator = sdd_validate.Validator(root, root, "current")
            validator._discover()
            phase = validator.by_path["Plans/Feature/01-Build.md"]
            validator._verify_git_phase_post_review_state(phase, phase, endpoint, 1)
            self.assertIn("SDD173", {item.code for item in validator.out})

    def test_git_phase_post_review_state_rejects_old_evidence_directory_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            endpoint = self.commit_all(root)
            evidence = root / "Plans/Feature/evidence/post-review.txt"
            evidence.parent.mkdir()
            evidence.write_text("material post-review content\n", encoding="utf-8")
            subprocess.run(["git", "add", str(evidence)], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "post-review evidence"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            validator = sdd_validate.Validator(root, root, "current")
            validator._discover()
            phase = validator.by_path["Plans/Feature/01-Build.md"]
            validator._verify_git_phase_post_review_state(phase, phase, endpoint, 1)
            self.assertIn("SDD173", {item.code for item in validator.out})

    def test_fenced_required_heading_is_not_a_real_section(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            plan = plan_document().replace(
                "## Plan Completion Evidence\n        Pending — not complete.",
                "````markdown\n        ## Plan Completion Evidence\n"
                "        Pending — not complete.\n        ````",
            )
            write(root, "Plans/Feature/README.md", plan)
            findings = [item for item in self.validate(root) if item.code == "SDD020"]
            self.assertTrue(
                any("Plan Completion Evidence" in item.message for item in findings)
            )

    def test_reports_status_drift_unknown_dependency_and_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            write(root, "Plans/Feature/README.md", plan_document(phase_status="blocked", depends_on="1"))
            write(root, "Plans/Feature/01-Build.md", phase_document(depends_on="1.1"))
            codes = {item.code for item in self.validate(root)}
            self.assertTrue({"SDD058", "SDD131", "SDD132", "SDD134", "SDD135"}.issubset(codes))

    def test_reports_review_and_decision_integrity_failures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            write(
                root,
                "Plans/Feature/reviews/01-feature-code-review-test.md",
                """
                ---
                title: Review
                type: review
                status: resolved
                created: 2026-07-21
                updated: 2026-07-21
                tags: [review]
                related: [Plans/Feature]
                review_of: Plans/Feature
                rev: test
                findings:
                  - id: F-01
                    severity: major
                    title: Deferred issue
                    status: open
                followups:
                  - id: FU-01
                    finding: F-01
                    summary: Follow up
                    tracked_in: ""
                ---
                # Review
                ## Findings
                ### F-01 — Major Deferred issue
                Scenario.
                ## Resolution Log
                None.
                """,
            )
            codes = {item.code for item in self.validate(root)}
            self.assertIn("SDD091", codes)
            self.assertIn("SDD095", codes)

    def test_cli_emits_machine_readable_json_and_nonzero_for_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            write(root, "Plans/Feature/README.md", plan_document(phase_status="blocked"))
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--root", str(root), "--format", "json"],
                check=False,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(1, completed.returncode)
            self.assertFalse(payload["valid"])
            self.assertTrue(payload["diagnostics"])

    def test_explicit_planning_root_preserves_invocation_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            root = repo / ".plans"
            (repo / ".git").mkdir(parents=True)
            root.mkdir()
            resolved_root, resolved_repo = sdd_validate.resolve_roots(PLUGIN_ROOT, str(root))
            self.assertEqual(root.resolve(), resolved_root)
            self.assertEqual(PLUGIN_ROOT.resolve(), resolved_repo)

    def test_task_ids_are_scoped_to_their_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            write(
                root,
                "Plans/Other/README.md",
                plan_document().replace("Feature Plan", "Other Plan").replace(
                    "Plans/Feature", "Plans/Other"
                ),
            )
            write(
                root,
                "Plans/Other/01-Build.md",
                phase_document().replace("plan: Feature", "plan: Other"),
            )
            codes = [item.code for item in self.validate(root)]
            self.assertNotIn("SDD031", codes)

    def test_cli_rejects_empty_root_and_unknown_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            empty = subprocess.run(
                [sys.executable, str(SCRIPT), "--root", str(root), "--format", "json"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, empty.returncode)
            self.make_valid_tree(root)
            unknown = subprocess.run(
                [sys.executable, str(SCRIPT), "--root", str(root), "--scope", "Typo", "--format", "json"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, unknown.returncode)
            self.assertIn("does not resolve", json.loads(unknown.stdout)["error"])

    def test_scoped_validation_follows_transitive_related_graph(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            spec_path = root / "Specs" / "Feature" / "README.md"
            spec_path.write_text(
                spec_path.read_text(encoding="utf-8").replace(
                    "related: []", "related: [Designs/Feature]", 1
                ),
                encoding="utf-8",
            )
            design = """
            ---
            title: Feature Design
            type: design
            status: approved
            created: 2026-07-23
            updated: 2026-07-23
            tags: [feature]
            related: [Research/legacy.txt]
            ---
            # Feature Design
            ## Overview
            Feature design.
            ## Design Decisions
            Decisions.
            ## Error Handling
            Errors.
            ## Testing Strategy
            Tests.
            ## Migration / Rollout
            Rollout.
            """
            write(root, "Designs/Feature/README.md", design)
            write(
                root,
                "Designs/Other/README.md",
                design.replace("Feature Design", "Other Design"),
            )
            legacy = root / "Research" / "legacy.txt"
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_text("not a discoverable SDD artifact\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "--scope",
                    "Plans/Feature/README.md",
                    "--format",
                    "json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(1, result.returncode, result.stderr)
            self.assertEqual(
                {
                    "Plans/Feature/README.md",
                    "Plans/Feature/01-Build.md",
                    "Specs/Feature/README.md",
                    "Designs/Feature/README.md",
                },
                set(payload["artifacts_in_scope"]),
            )
            self.assertTrue(
                any(item["path"] == "Designs/Feature/README.md" for item in payload["diagnostics"])
            )
            self.assertFalse(
                any(item["path"] == "Designs/Other/README.md" for item in payload["diagnostics"])
            )
            self.assertNotIn("Research/legacy.txt", payload["artifacts_in_scope"])

    def test_scope_aliases_resolve_or_report_ambiguity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            write(
                root,
                "Research/Topic.md",
                """
                ---
                title: Topic
                type: research
                status: active
                created: 2026-07-23
                updated: 2026-07-23
                tags: [topic]
                related: []
                ---
                # Topic
                ## Context
                Context.
                ## Findings
                Findings.
                ## Analysis
                Analysis.
                ## Open Questions
                None.
                """,
            )
            validator = sdd_validate.Validator(root, root)
            diagnostics = validator.run()
            alias = sdd_validate.resolve_scope(validator, "Specs/Feature/README")
            self.assertIsNone(alias.error)
            self.assertIn("Specs/Feature/README.md", alias.artifacts)

            flat = sdd_validate.resolve_scope(validator, "Topic")
            self.assertIsNone(flat.error)
            self.assertEqual(frozenset({"Research/Topic.md"}), flat.artifacts)

            ambiguous = sdd_validate.resolve_scope(validator, "Feature")
            self.assertIn("ambiguous", ambiguous.error or "")
            self.assertEqual(
                ("Plans/Feature", "Specs/Feature/README.md"),
                ambiguous.roots,
            )

            deleted = sdd_validate.resolve_scope(
                validator,
                "Specs/Deleted/README.md",
                diagnostics
                + [
                    sdd_validate.Diagnostic(
                        "error",
                        "SDD164",
                        "Specs/Deleted/README.md",
                        1,
                        "deleted",
                        "restore",
                    )
                ],
            )
            self.assertIsNone(deleted.error)
            self.assertEqual(("Specs/Deleted/README.md",), deleted.roots)

            (root / "README.md").write_text("ordinary repository file\n", encoding="utf-8")
            for unsafe in ("README.md", "../outside", str(root / "README.md")):
                self.assertIsNotNone(
                    sdd_validate.resolve_scope(validator, unsafe, diagnostics).error
                )

            write(root, "Plans/Mixed/README.md", plan_document().replace("Feature Plan", "Mixed Plan"))
            write(root, "Specs/Mixed/README.md", "not frontmatter\n")
            mixed_validator = sdd_validate.Validator(root, root)
            mixed_diagnostics = mixed_validator.run()
            mixed = sdd_validate.resolve_scope(
                mixed_validator, "Mixed", mixed_diagnostics
            )
            self.assertIn("ambiguous", mixed.error or "")
            self.assertEqual(
                ("Plans/Mixed", "Specs/Mixed/README.md"),
                mixed.roots,
            )

    def test_scoped_malformed_artifact_keeps_parse_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            malformed = root / "Plans" / "Feature" / "02-Broken.md"
            malformed.write_text("not frontmatter\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "--scope",
                    "Plans/Feature",
                    "--format",
                    "json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(1, result.returncode, result.stderr)
            self.assertTrue(
                any(
                    item["path"] == "Plans/Feature/02-Broken.md"
                    and item["code"] == "SDD004"
                    for item in payload["diagnostics"]
                )
            )
            self.assertNotIn("Plans/Feature/02-Broken.md", payload["artifacts_in_scope"])

            malformed_spec = root / "Specs" / "Feature" / "extra.md"
            malformed_spec.write_text("not frontmatter\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "--scope",
                    "Specs/Feature",
                    "--format",
                    "json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(1, result.returncode, result.stderr)
            self.assertTrue(
                any(item["path"] == "Specs/Feature/extra.md" for item in payload["diagnostics"])
            )

    def test_graph_selection_preserves_global_diagnostics_and_candidates(self) -> None:
        diagnostics = [
            sdd_validate.Diagnostic("error", "SDD020", "Designs/Feature/README.md", 1, "feature", "fix"),
            sdd_validate.Diagnostic("error", "SDD020", "Designs/Other/README.md", 1, "other", "fix"),
            sdd_validate.Diagnostic("candidate", "DLG060", "Decisions/decisions.md", 1, "candidate", "judge"),
            sdd_validate.Diagnostic("error", "SDD145", "Decisions/decisions.md", 1, "decision scope", "fix"),
            sdd_validate.Diagnostic("operational", "SDD999", "outside", 1, "operation", "repair"),
        ]
        selected = sdd_validate.select(
            diagnostics,
            "Plans/Feature",
            {"Plans/Feature/README.md", "Designs/Feature/README.md"},
        )
        self.assertEqual(
            {"feature", "candidate", "decision scope", "operation"},
            {item.message for item in selected},
        )

    def test_external_plan_mapping_loads_target_repository_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            coordinator = base / "coordinator"
            root = base / "planning"
            target = base / "target"
            (coordinator / ".git").mkdir(parents=True)
            target.mkdir()
            self.make_valid_tree(root)
            plan_path = root / "Plans/Feature/README.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "## Key Decisions\nNone.", "## Key Decisions\nUse the target repository ledger (D-0001)."
                ),
                encoding="utf-8",
            )
            (coordinator / "planning-config.json").write_text(
                json.dumps(
                    {
                        "planningRoot": str(root),
                        "repositories": {"target": {"path": str(target)}},
                        "planMapping": {"Feature": "target"},
                    }
                ),
                encoding="utf-8",
            )
            write(
                target,
                "DECISIONS.md",
                """
                ---
                title: Target Decisions
                type: decision-log
                status: active
                created: 2026-07-21
                updated: 2026-07-21
                tags: [decisions]
                related: []
                decisions:
                  - id: D-0001
                    kind: decision
                    status: accepted
                    date: 2026-07-21
                    decided_by: user
                    statement: Use the target repository.
                    rationale: It owns implementation.
                    scope: [Plans/Feature]
                    tags: [target]
                    rejected: []
                ---
                # Target Decisions
                """,
            )
            diagnostics = sdd_validate.Validator(root, coordinator).run()
            codes = {item.code for item in diagnostics}
            self.assertNotIn("SDD120", codes)
            self.assertNotIn("SDD145", codes)
            self.assertNotIn("SDD146", codes)

    def test_related_scopes_expose_conflicting_definitions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            spec_path = root / "Specs/Feature/README.md"
            spec_path.write_text(
                spec_path.read_text(encoding="utf-8").replace(
                    "Feature overview.", "Feature overview governed by D-0001."
                ),
                encoding="utf-8",
            )
            write(
                root,
                "Designs/Feature/README.md",
                """
                ---
                title: Feature Design
                type: design
                status: approved
                created: 2026-07-21
                updated: 2026-07-21
                tags: [feature]
                related: [Specs/Feature]
                ---
                # Feature Design
                ## Overview
                Governed by D-0002.
                ## Architecture
                Architecture.
                ## Design Decisions
                Decisions.
                ## Error Handling
                Errors.
                ## Testing Strategy
                Tests.
                ## Migration / Rollout
                Rollout.
                """,
            )
            write(
                root,
                "Decisions/decisions.md",
                """
                ---
                title: Decision Ledger
                type: decision-log
                status: active
                created: 2026-07-21
                updated: 2026-07-21
                tags: [decisions]
                related: []
                decisions:
                  - id: D-0001
                    kind: definition
                    status: accepted
                    date: 2026-07-21
                    decided_by: user
                    statement: Widget means the first behavior.
                    rationale: First definition.
                    scope: [Specs/Feature]
                    tags: [widget]
                    rejected: []
                  - id: D-0002
                    kind: definition
                    status: accepted
                    date: 2026-07-21
                    decided_by: user
                    statement: Widget means the second behavior.
                    rationale: Second definition.
                    scope: [Designs/Feature]
                    tags: [widget]
                    rejected: []
                ---
                # Decision Ledger
                """,
            )
            codes = {item.code for item in self.validate(root)}
            self.assertIn("SDD149", codes)

    def test_absolute_and_parent_related_paths_do_not_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            plan = plan_document().replace(
                "related: [Specs/Feature]",
                "related: [/Specs/Feature, ../Specs/Feature]",
            )
            write(root, "Plans/Feature/README.md", plan)
            related_errors = [
                item for item in self.validate(root) if item.code == "SDD041"
            ]
            self.assertEqual(2, len(related_errors))

    def test_evidence_rows_preserve_kind_and_nonpassing_results(self) -> None:
        rows = sdd_validate.evidence_rows(textwrap.dedent(
            """
            | Command | Working directory | Result | Observable evidence |
            |---|---|---|---|
            | `pytest` | `/repo` | SKIPPED | Not executed. |

            | Tool / inspection | Context | Result | Observable evidence |
            |---|---|---|---|
            | `reviewer` | `file` | PASS | Inspected. |
            """
        ))
        self.assertEqual("command", rows[0][0])
        self.assertEqual(("pytest", "/repo", "SKIPPED", "Not executed."), rows[0][1])
        self.assertEqual("SKIPPED", rows[0][1][2])
        self.assertEqual("tool", rows[1][0])
        formatted_headers = sdd_validate.evidence_rows(
            """
            | **Command** | _Working directory_ | <em>Result</em> | `Observable evidence` |
            |---|---|---|---|
            | `pytest` | `/repo` | PASS (`exit 0`) | Formatted command header parsed. |

            | **Tool / inspection** | _Context_ | <em>Result</em> | `Observable evidence` |
            |---|---|---|---|
            | `reviewer` | `file` | PASS | Formatted tool header parsed. |
            """
        )
        self.assertEqual([], formatted_headers)
        fenced = """
            ````markdown
            | Command | Working directory | Result | Observable evidence |
            |---|---|---|---|
            | `fake` | `/repo` | PASS (`exit 0`) | Only an example. |
            ````
        """
        self.assertEqual([], sdd_validate.evidence_rows(textwrap.dedent(fenced)))
        task_body = """
            ### Notes
            ````markdown
            ### Completion Evidence
            Pending — not complete.
            ````
            ### Completion Evidence
            proof <!-- annotation --> retained
        """
        evidence = sdd_validate.completion_evidence_body(textwrap.dedent(task_body))
        self.assertEqual("proof  retained", evidence)

    def test_fenced_spec_definition_does_not_preserve_append_only_id(self) -> None:
        source = spec_document().replace(
            "- **FR-01**: Do the thing.",
            "````markdown\n        - **FR-01**: Do the thing.\n        ````\n"
            "        - **FR-02**: Replacement.",
        )
        self.assertNotIn("FR-01", sdd_validate.spec_retained_ids(textwrap.dedent(source)))

    def test_plan_review_inherits_specs_and_tracks_followup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            write(
                root,
                "Specs/Feature/reviews/01-feature-code-review-test.md",
                """
                ---
                title: Feature Review
                type: review
                status: resolved
                created: 2026-07-21
                updated: 2026-07-21
                tags: [review]
                related: [Specs/Feature, Plans/Feature]
                review_of: Specs/Feature
                rev: test
                findings:
                  - id: F-01
                    severity: major
                    title: Follow-up required
                    status: deferred
                followups:
                  - id: FU-01
                    finding: F-01
                    summary: Implement the requirement
                    tracked_in: "1.1"
                ---
                # Feature Review
                ## Findings
                ### F-01 — Major Follow-up required
                **Impugns:** FR-01 and AC-01.
                ## Resolution Log
                ### F-01 — deferred (2026-07-21)
                Tracked in task 1.1.
                """,
            )
            findings = self.validate(root)
            codes = {item.code for item in findings}
            self.assertNotIn("SDD096", codes)
            self.assertNotIn("SDD098", codes)
            self.assertNotIn("SDD122", codes)

    def test_review_supersession_requires_lifecycle_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            old_path = "Plans/Feature/reviews/01-feature-code-review-old.md"
            new_path = "Plans/Feature/reviews/02-feature-code-review-new.md"
            write(
                root,
                old_path,
                f"""
                ---
                title: Old Review
                type: review
                status: open
                created: 2026-07-21
                updated: 2026-07-21
                tags: [review]
                related: [Plans/Feature]
                review_of: Plans/Feature
                rev: old
                findings: []
                followups: []
                superseded_by: {new_path}
                ---
                # Old Review
                ## Findings
                None.
                ## Resolution Log
                None.
                """,
            )
            write(
                root,
                new_path,
                f"""
                ---
                title: New Review
                type: review
                status: open
                created: 2026-07-21
                updated: 2026-07-21
                tags: [review]
                related: [Plans/Feature]
                review_of: Plans/Feature
                rev: new
                findings: []
                followups: []
                supersedes: {old_path}
                ---
                # New Review
                ## Findings
                None.
                ## Resolution Log
                None.
                """,
            )
            codes = {item.code for item in self.validate(root)}
            self.assertIn("SDD099", codes)
            self.assertIn("SDD102", codes)

    def test_no_vcs_nested_start_finds_parent_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            nested = repo / "a" / "b"
            nested.mkdir(parents=True)
            (repo / ".plans").mkdir()
            (repo / "planning-config.json").write_text(
                json.dumps({"planningRoot": ".plans"}), encoding="utf-8"
            )
            root, resolved_repo = sdd_validate.resolve_roots(nested, None)
            self.assertEqual((repo / ".plans").resolve(), root)
            self.assertEqual(repo.resolve(), resolved_repo)

    def test_active_plan_requires_requirement_and_acceptance_citations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            phase = phase_document().replace("NFR-01", "unlinked-NFR").replace(
                "AC-01", "unlinked-AC"
            )
            write(root, "Plans/Feature/01-Build.md", phase)
            codes = {item.code for item in self.validate(root)}
            self.assertIn("SDD160", codes)
            self.assertIn("SDD162", codes)
            validator = sdd_validate.Validator(root, root)
            scoped = sdd_validate.select(validator.run(), "Specs/Feature")
            self.assertTrue(any(item.code in {"SDD160", "SDD162"} for item in scoped))

    def test_clean_git_identity_checks_immutable_ancestor_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.com",
                    "commit",
                    "-m",
                    "fixture",
                ],
                cwd=root,
                check=True,
                capture_output=True,
            )
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            validator = sdd_validate.Validator(root, root, "current")
            validator._discover()
            plan = validator.by_path["Plans/Feature/README.md"]
            validator._verify_clean_git_identity(
                plan, revision, "Plan Completion Evidence", 1, True
            )
            self.assertEqual([], validator.out)
            (root / "changed.txt").write_text("changed", encoding="utf-8")
            validator._verify_clean_git_identity(
                plan, revision, "Plan Completion Evidence", 1, True
            )
            self.assertEqual([], validator.out)

    def test_clean_git_evidence_uses_commits_without_evidence_folder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            implementation_revision = self.commit_all(root)
            block = f"""
            - Verified: 2026-07-23
            - Repository: `{root}`
            - VCS: `git`
            - Revision / checkpoint: `{implementation_revision}`
            - Identity recheck: `git diff-tree --exit-code {implementation_revision}`, 2026-07-23T12:00:00Z, matched commit tree

            | Command | Working directory | Result | Observable evidence |
            |---|---|---|---|
            | `python3 -m unittest` | `{root}` | PASS (`exit 0`) | Named behavior passed. |
            """
            phase = phase_document(task_status="complete")
            phase = phase.replace("- [ ] Implement it.", "- [x] Implement it.")
            indented_block = textwrap.dedent(block).strip().replace("\n", "\n        ")
            phase = phase.replace(
                "Pending — not complete.", indented_block, 1
            )
            write(root, "Plans/Feature/01-Build.md", phase)
            subprocess.run(["git", "add", "Plans/Feature/01-Build.md"], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.com",
                    "commit",
                    "-m",
                    "Record task completion",
                ],
                cwd=root,
                check=True,
                capture_output=True,
            )

            findings = sdd_validate.Validator(root, root, "current").run()
            evidence_findings = {
                item.code for item in findings if "Task 1.1 Completion Evidence" in item.message
            }
            self.assertFalse({"SDD071", "SDD072", "SDD074"} & evidence_findings)
            self.assertFalse((root / "evidence").exists())

            phase_path = root / "Plans" / "Feature" / "01-Build.md"
            phase_path.write_text(
                phase_path.read_text(encoding="utf-8").replace(
                    "Named behavior passed.", "Uncommitted evidence edit."
                ),
                encoding="utf-8",
            )
            findings = sdd_validate.Validator(root, root, "current").run()
            self.assertTrue(
                any("differs from its committed section" in item.message for item in findings)
            )

    def test_uncommitted_task_completion_transition_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            implementation_revision = self.commit_all(root)
            block = f"""
            - Verified: 2026-07-23
            - Repository: `{root}`
            - VCS: `git`
            - Revision / checkpoint: `{implementation_revision}`
            - Identity recheck: `git diff-tree --exit-code {implementation_revision}`, 2026-07-23T12:00:00Z, matched commit tree

            | Command | Working directory | Result | Observable evidence |
            |---|---|---|---|
            | `python3 -m unittest` | `{root}` | PASS (`exit 0`) | Named behavior passed. |
            """
            indented = textwrap.dedent(block).strip().replace("\n", "\n        ")
            phase = phase_document(task_status="in-progress").replace(
                "Pending — not complete.", indented, 1
            )
            write(root, "Plans/Feature/01-Build.md", phase)
            subprocess.run(["git", "add", "Plans/Feature/01-Build.md"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "Stage evidence"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            phase_path = root / "Plans" / "Feature" / "01-Build.md"
            source = phase_path.read_text(encoding="utf-8")
            source = source.replace("status: in-progress", "status: complete", 1)
            source = source.replace("- [ ] Implement it.", "- [x] Implement it.")
            phase_path.write_text(source, encoding="utf-8")

            findings = sdd_validate.Validator(root, root, "current").run()
            self.assertTrue(
                any("lifecycle completion is not committed" in item.message for item in findings)
            )

    def test_clean_git_rejects_every_fallback_only_field(self) -> None:
        body = """
        - Verified: 2026-07-23
        - Repository: `/tmp/repo`
        - VCS: `git`
        - Revision / base: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
        - Identity recheck: `git`, 2026-07-23T12:00:00Z, matched commit
        - Ignored inputs: `none with inspection basis`

        | Tool / inspection | Context | Result | Observable evidence |
        |---|---|---|---|
        | `inspection` | `repo` | PASS | Clean commit inspected. |
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            validator = sdd_validate.Validator(root, root, "historical")
            validator._discover()
            artifact = validator.by_path["Plans/Feature/README.md"]
            validator._evidence(
                artifact,
                "in-progress",
                "Plan Completion Evidence",
                1,
                textwrap.dedent(body),
            )
            self.assertTrue(any(item.code == "SDD074" for item in validator.out))

    def test_phase_completion_requires_committed_parent_plan_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            self.commit_all(root)
            evidence = """
            - Verified: 2026-07-23
            - Repository: `/tmp/example`
            - VCS: `git`
            - Revision / checkpoint: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
            - Identity recheck: `git aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`, 2026-07-23T12:00:00Z, matched commit

            | Tool / inspection | Context | Result | Observable evidence |
            |---|---|---|---|
            | `inspection` | `phase` | PASS | Phase behavior passed. |
            """
            indented = textwrap.dedent(evidence).strip().replace("\n", "\n        ")
            phase = phase_document()
            phase = phase.replace("status: planned", "status: complete", 1)
            phase = phase.replace("- [ ] AC-01", "- [x] AC-01")
            phase = phase.replace("Pending — not complete.", indented, 2)
            write(root, "Plans/Feature/01-Build.md", phase)
            subprocess.run(["git", "add", "Plans/Feature/01-Build.md"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "Complete phase artifact"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            plan_path = root / "Plans" / "Feature" / "README.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "status: planned", "status: complete", 1
                ),
                encoding="utf-8",
            )
            validator = sdd_validate.Validator(root, root, "current")
            validator._discover()
            artifact = validator.by_path["Plans/Feature/01-Build.md"]
            validator._verify_evidence_committed(
                artifact,
                "Phase Completion Evidence",
                textwrap.dedent(evidence).strip(),
                1,
            )
            self.assertTrue(
                any("lifecycle completion is not committed" in item.message for item in validator.out)
            )

    def test_completed_task_identities_match_documented_grammar(self) -> None:
        artifact = sdd_validate.Artifact(Path("phase.md"), "phase.md", {}, "", "", 1)
        validator = sdd_validate.Validator(Path("."), Path("."))
        body = (
            "### Completed task identities\n"
            "- `1.1`: `<native implementation revision/checkpoint>`\n"
        )
        validator._completed_identities(
            artifact,
            body,
            "Completed task identities",
            {"1.1": "<native implementation revision/checkpoint>"},
            1,
            "task",
        )
        self.assertEqual([], validator.out)
        for invalid in (
            body + "- `1.1`: `<native implementation revision/checkpoint>`\n",
            "### Completed task identities\n",
            "### Completed task identities\n- `1.2`: `<native implementation revision/checkpoint>`\n",
            "### Completed task identities\n- `1.1`: `different`\n",
            "### Completed task identities\n- 1.1: <native implementation revision/checkpoint>\n",
            "### Completed task identities\n- `1.1`: `<native implementation revision/checkpoint>\n",
            "### Completed task identities\n- `1.1`: `<native implementation revision/checkpoint>`; review: `Plans/Feature/reviews/01-final.md`\n",
            "### Task 1.1 Evidence Rollup\nproof\n",
        ):
            validator.out.clear()
            validator._completed_identities(
                artifact,
                invalid,
                "Completed task identities",
                {"1.1": "<native implementation revision/checkpoint>"},
                1,
                "task",
            )
            self.assertIn("SDD157", {item.code for item in validator.out})

    def test_completed_phase_identities_match_documented_grammar(self) -> None:
        artifact = sdd_validate.Artifact(Path("plan.md"), "plan.md", {}, "", "", 1)
        validator = sdd_validate.Validator(Path("."), Path("."))
        body = (
            "### Completed phase identities\n"
            "- `1`: `<phase completion revision/checkpoint>`; review: `<final review artifact path>`\n"
        )
        expected = {
            "1": (
                "<phase completion revision/checkpoint>",
                "<final review artifact path>",
            )
        }
        validator._completed_identities(
            artifact, body, "Completed phase identities", expected, 1, "phase"
        )
        self.assertEqual([], validator.out)
        for invalid in (
            body + "- `1`: `<phase completion revision/checkpoint>`; review: `<final review artifact path>`\n",
            "### Completed phase identities\n",
            "### Completed phase identities\n- `2`: `<phase completion revision/checkpoint>`; review: `<final review artifact path>`\n",
            "### Completed phase identities\n- `1`: `different`; review: `<final review artifact path>`\n",
            "### Completed phase identities\n- 1: <phase completion revision/checkpoint>; review: <final review artifact path>\n",
            "### Completed phase identities\n- `1`: `<phase completion revision/checkpoint>`; review: `<final review artifact path>\n",
            "### Completed phase identities\n- `1`: `<phase completion revision/checkpoint>`; review: `<final review artifact path>`; extra: `suffix`\n",
            "### Completed phase identities\n- `1`: `<phase completion revision/checkpoint>`\n",
            "### Phase 1 Evidence Rollup\nproof\n",
        ):
            validator.out.clear()
            validator._completed_identities(
                artifact, invalid, "Completed phase identities", expected, 1, "phase"
            )
            self.assertIn("SDD158", {item.code for item in validator.out})

    def test_git_plan_checkpoint_contains_completed_phase_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            base = self.commit_all(root)
            (root / "phase-checkpoint.txt").write_text("phase\n", encoding="utf-8")
            subprocess.run(["git", "add", "phase-checkpoint.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "phase checkpoint"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            phase_checkpoint = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
            ).stdout.strip()
            (root / "plan-checkpoint.txt").write_text("plan\n", encoding="utf-8")
            subprocess.run(["git", "add", "plan-checkpoint.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "plan checkpoint"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            plan_checkpoint = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
            ).stdout.strip()
            phase_evidence = f"- VCS: `git`\n- Revision / checkpoint: `{phase_checkpoint}`"
            indented_phase_evidence = phase_evidence.replace("\n", "\n        ")
            write(
                root,
                "Plans/Feature/01-Build.md",
                phase_document().replace("Pending — not complete.", indented_phase_evidence),
            )
            write(root, "Plans/Feature/README.md", plan_document(phase_status="complete"))
            validator = sdd_validate.Validator(root, root, "historical")
            validator._discover()
            plan = validator.by_path["Plans/Feature/README.md"]
            phases = plan.meta["phases"]
            plan_evidence = f"- VCS: `git-worktree`\n- Revision / checkpoint: `{plan_checkpoint}`"
            validator._verify_git_plan_phase_checkpoints(plan, phases, plan_evidence, 1)
            self.assertNotIn("SDD175", {item.code for item in validator.out})

            validator.out.clear()
            validator._verify_git_plan_phase_checkpoints(
                plan,
                phases,
                f"- VCS: `git`\n- Revision / checkpoint: `{base}`",
                1,
            )
            self.assertIn("SDD175", {item.code for item in validator.out})

            validator.out.clear()
            write(
                root,
                "Plans/Feature/01-Build.md",
                phase_document().replace(
                    "Pending — not complete.",
                    "- VCS: `git`\n        - Revision / checkpoint: `" + "a" * 40 + "`",
                ),
            )
            validator._discover()
            plan = validator.by_path["Plans/Feature/README.md"]
            validator._verify_git_plan_phase_checkpoints(plan, plan.meta["phases"], plan_evidence, 1)
            self.assertIn("SDD175", {item.code for item in validator.out})

            validator.out.clear()
            write(
                root,
                "Plans/Feature/01-Build.md",
                phase_document().replace(
                    "Pending — not complete.",
                    "- VCS: `perforce`\n        - Revision / checkpoint: `42`",
                ),
            )
            validator._discover()
            plan = validator.by_path["Plans/Feature/README.md"]
            validator._verify_git_plan_phase_checkpoints(plan, plan.meta["phases"], plan_evidence, 1)
            self.assertIn("SDD175", {item.code for item in validator.out})

            validator.out.clear()
            write(
                root,
                "Plans/Feature/01-Build.md",
                phase_document().replace("Pending — not complete.", indented_phase_evidence),
            )
            validator._discover()
            plan = validator.by_path["Plans/Feature/README.md"]
            phase = validator.by_path["Plans/Feature/01-Build.md"]
            validator.artifact_repos[phase.rel] = root / "other-repository"
            validator._verify_git_plan_phase_checkpoints(plan, plan.meta["phases"], plan_evidence, 1)
            self.assertIn("SDD175", {item.code for item in validator.out})

    def test_phase_review_lane_results_are_complete_and_auditable(self) -> None:
        revision = "b" * 40
        meta = {
            "rev": revision,
            "reviewed_planning_revision": "a" * 40,
            "review_mode": "independent",
            "lane_results": [
                {"lane": "review_plan_drift", "result": "PASS/Aligned", "reviewed_identity": revision, "evidence": "Phase checklist compared against task evidence."},
                {"lane": "review_quality", "result": "PASS/Aligned", "reviewed_identity": revision, "evidence": "Changed implementation paths inspected."},
                {"lane": "review_spec_compliance", "result": "PASS/Aligned", "reviewed_identity": revision, "evidence": "Acceptance criteria compared to implementation."},
                {"lane": "review_blind_spots", "result": "PASS/Aligned", "reviewed_identity": revision, "evidence": "Empty-input branches inspected."},
            ],
        }
        self.assertEqual([], sdd_validate.phase_review_schema_errors(meta))
        meta["reviewed_phase_intent_sha256"] = "a" * 64
        self.assertTrue(sdd_validate.phase_review_schema_errors(meta))

    def test_phase_review_lifecycle_normalization_allows_lifecycle_changes_and_rejects_nested_policy_status_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            planning_root = Path(directory) / "planning"
            target_repository = Path(directory) / "target"
            planning_root.mkdir()
            target_repository.mkdir()
            self.make_valid_tree(planning_root)
            phase_path = planning_root / "Plans/Feature/01-Build.md"
            phase_path.write_text(
                phase_path.read_text(encoding="utf-8").replace(
                    "deliverable: Feature implementation",
                    "deliverable: Feature implementation\npolicy:\n  status: retained",
                    1,
                ),
                encoding="utf-8",
            )
            reviewed = self.commit_all(planning_root)
            validator = sdd_validate.Validator(planning_root, target_repository)
            validator._discover()
            phase = validator.by_path["Plans/Feature/01-Build.md"]
            review = sdd_validate.Artifact(
                planning_root / "Plans/Feature/reviews/01-final.md",
                "Plans/Feature/reviews/01-final.md",
                {"reviewed_planning_revision": reviewed}, "", "", 1,
            )
            validator._verify_phase_review_planning_revision(phase, review, 1)
            self.assertNotIn("SDD174", {item.code for item in validator.out})
            phase.path.write_text(
                phase.path.read_text(encoding="utf-8").replace("status: planned", "status: in-progress", 1),
                encoding="utf-8",
            )
            validator = sdd_validate.Validator(planning_root, target_repository)
            validator._discover()
            phase = validator.by_path["Plans/Feature/01-Build.md"]
            validator._verify_phase_review_planning_revision(phase, review, 1)
            self.assertNotIn("SDD174", {item.code for item in validator.out})
            phase.path.write_text(
                phase.path.read_text(encoding="utf-8").replace("status: retained", "status: changed", 1),
                encoding="utf-8",
            )
            validator = sdd_validate.Validator(planning_root, target_repository)
            validator._discover()
            validator._verify_phase_review_planning_revision(
                validator.by_path["Plans/Feature/01-Build.md"], review, 1
            )
            self.assertIn("SDD174", {item.code for item in validator.out})
            subprocess.run(
                ["git", "add", "Plans/Feature/01-Build.md"],
                cwd=planning_root,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.com",
                    "commit",
                    "-m",
                    "later phase intent revision",
                ],
                cwd=planning_root,
                check=True,
                capture_output=True,
            )
            current = sdd_validate.Validator(planning_root, target_repository, "current")
            current._discover()
            current._verify_phase_review_planning_revision(
                current.by_path["Plans/Feature/01-Build.md"], review, 1
            )
            self.assertIn("SDD174", {item.code for item in current.out})
            historical = sdd_validate.Validator(planning_root, target_repository, "historical")
            historical._discover()
            historical._verify_phase_review_planning_revision(
                historical.by_path["Plans/Feature/01-Build.md"], review, 1
            )
            self.assertNotIn("SDD174", {item.code for item in historical.out})
            phase_path.write_text(
                phase_path.read_text(encoding="utf-8").replace("status: changed", "status: retained", 1),
                encoding="utf-8",
            )
            plan_path = planning_root / "Plans/Feature/README.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace("Build the feature.", "Build a different feature."),
                encoding="utf-8",
            )
            validator = sdd_validate.Validator(planning_root, target_repository)
            validator._discover()
            validator._verify_phase_review_planning_revision(
                validator.by_path["Plans/Feature/01-Build.md"], review, 1
            )
            self.assertIn("SDD174", {item.code for item in validator.out})
            review.meta["reviewed_planning_revision"] = "f" * 40
            historical.out.clear()
            historical._verify_phase_review_planning_revision(
                historical.by_path["Plans/Feature/01-Build.md"], review, 1
            )
            self.assertIn("SDD174", {item.code for item in historical.out})

    def test_full_validator_and_cli_report_unsupported_current_lifecycle_nodes(self) -> None:
        cases = (
            (
                "flow phase task",
                "Plans/Feature/01-Build.md",
                (
                    "tasks:\n"
                    '  - id: "1.1"\n'
                    "    title: Implement\n"
                    "    status: complete\n"
                    '    verification: "Run tests and satisfy FR-01, NFR-01, and AC-01"'
                ),
                (
                    "tasks: [{id: '1.1', title: Implement, status: complete, "
                    'verification: "Run tests and satisfy FR-01, NFR-01, and AC-01"}]'
                ),
            ),
            (
                "multiline plan status",
                "Plans/Feature/README.md",
                "status: complete",
                "status: |\n  complete",
            ),
        )
        for name, relative, original, replacement in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.make_valid_tree(root)
                self.complete_phase_and_plan(root)
                path = root / relative
                path.write_text(
                    path.read_text(encoding="utf-8").replace(original, replacement, 1),
                    encoding="utf-8",
                )

                findings = sdd_validate.Validator(root, root, "current").run()
                self.assertIn("SDD174", {item.code for item in findings})

                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "--root", str(root)],
                    cwd=root,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(1, result.returncode)
                self.assertIn("ERROR SDD174", result.stdout)
                self.assertNotIn("Traceback", result.stderr)

    def test_completion_rejects_dirty_no_scm_and_synthetic_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            validator = sdd_validate.Validator(root, root, "historical")
            validator._discover()
            artifact = validator.by_path["Plans/Feature/README.md"]
            body = f"""
            - Verified: 2026-07-23
            - Repository: `{root}`
            - VCS: `git`
            - Revision / checkpoint: `{'a' * 40}-dirty`
            - Governing intent: `removed`
            - Identity recheck: `git`, 2026-07-23T12:00:00Z, matched commit

            | Tool / inspection | Context | Result | Observable evidence |
            |---|---|---|---|
            | `inspection` | `repo` | PASS | Clean commit inspected. |
            """
            validator._evidence(artifact, "in-progress", "Plan Completion Evidence", 1, textwrap.dedent(body))
            self.assertTrue({"SDD072", "SDD074"}.issubset({item.code for item in validator.out}))
            validator.out.clear()
            none = body.replace("VCS: `git`", "VCS: `none`").replace(
                f"`{'a' * 40}-dirty`", "`none`"
            ).replace("- Governing intent: `removed`\n", "")
            validator._evidence(artifact, "complete", "Plan Completion Evidence", 1, textwrap.dedent(none))
            self.assertIn("SDD172", {item.code for item in validator.out})

    def test_phase_review_schema_rejects_short_planning_revision(self) -> None:
        self.assertIn(
            "reviewed_planning_revision must be a full 40-hex Git commit",
            sdd_validate.phase_review_schema_errors(
                {"reviewed_planning_revision": "short", "review_mode": "independent", "lane_results": []}
            ),
        )

    def test_evidence_labels_are_unique_visible_entries(self) -> None:
        artifact = sdd_validate.Artifact(Path("plan.md"), "plan.md", {"type": "plan"}, "", "", 1)
        validator = sdd_validate.Validator(Path("."), Path("."), "historical")
        body = textwrap.dedent(
            """
            - Verified: 2026-07-23
            - Repository: `/repo`
            - VCS: `none`
            - Revision / checkpoint: `none`
            - Identity recheck: `inspection`, 2026-07-23T12:00:00Z, matched none

            | Tool / inspection | Context | Result | Observable evidence |
            |---|---|---|---|
            | `inspection` | `repo` | PASS | Aggregate state inspected. |
            """
        )
        fenced_and_commented = body + textwrap.dedent(
            """
            <!--
            - VCS: `git`
            -->
            ```markdown
            - VCS: `git`
            ```
            """
        )
        validator._evidence(artifact, "in-progress", "Plan Completion Evidence", 1, fenced_and_commented)
        self.assertNotIn("SDD071", {item.code for item in validator.out})
        validator.out.clear()
        validator._evidence(
            artifact,
            "in-progress",
            "Plan Completion Evidence",
            1,
            body + "- VCS: `none`\n",
        )
        self.assertIn("SDD071", {item.code for item in validator.out})

        task = sdd_validate.Artifact(Path("phase.md"), "phase.md", {"type": "phase"}, "", "", 1)
        validator.out.clear()
        validator._task_review_evidence(
            task,
            "Task 1.1 Completion Evidence",
            "- Focused review: `inspect`\n- Focused review: `inspect`\n- Reviewed candidate / final: `none`\n- Review result: PASS/Aligned\n",
            "none",
            "none",
            1,
        )
        self.assertIn("SDD169", {item.code for item in validator.out})

        validator.out.clear()
        phase = sdd_validate.Artifact(Path("phase.md"), "phase.md", {"type": "phase"}, "", "", 1)
        validator._phase_final_review(
            phase,
            "- Final aligned review: `one`; frozen: `a`\n- Final aligned review: `two`; frozen: `b`\n",
            1,
        )
        self.assertIn("SDD166", {item.code for item in validator.out})

    def test_indented_comment_terminator_exposes_duplicate_and_failing_evidence(self) -> None:
        body = textwrap.dedent(
            """
            - Verified: 2026-07-23
            - Repository: `/repo`
            - VCS: `none`
            - Revision / checkpoint: `none`
            - Identity recheck: `inspection`, 2026-07-23T12:00:00Z, matched none

            | Tool / inspection | Context | Result | Observable evidence |
            |---|---|---|---|
            | `inspection` | `repo` | PASS | Aggregate state inspected. |
            <!-- hidden evidence
                -->
            - VCS: `none`
            | Tool / inspection | Context | Result | Observable evidence |
            |---|---|---|---|
            | `inspection` | `repo` | FAIL | Duplicate evidence was visible. |
            """
        )
        validator = sdd_validate.Validator(Path("."), Path("."), "historical")
        artifact = sdd_validate.Artifact(Path("plan.md"), "plan.md", {"type": "plan"}, "", "", 1)
        validator._evidence(artifact, "in-progress", "Plan Completion Evidence", 1, body)
        self.assertTrue({"SDD071", "SDD073"}.issubset({item.code for item in validator.out}))

    def test_unterminated_comment_inside_fence_does_not_hide_following_markdown(self) -> None:
        body = textwrap.dedent(
            """
            - Verified: 2026-07-23
            - Repository: `/repo`
            - VCS: `none`
            - Revision / checkpoint: `none`
            - Identity recheck: `inspection`, 2026-07-23T12:00:00Z, matched none

            ```markdown
            <!-- literal comment in example code
            ```
            - VCS: `none`
            ### Task 1.1 Evidence Rollup
            Legacy proof.
            """
        )
        validator = sdd_validate.Validator(Path("."), Path("."), "historical")
        plan = sdd_validate.Artifact(Path("plan.md"), "plan.md", {"type": "plan"}, "", "", 1)
        validator._evidence(plan, "in-progress", "Plan Completion Evidence", 1, body)
        self.assertIn("SDD071", {item.code for item in validator.out})

        validator.out.clear()
        phase = sdd_validate.Artifact(Path("phase.md"), "phase.md", {"type": "phase"}, body, "", 1)
        validator._headings(phase)
        self.assertIn("SDD157", {item.code for item in validator.out})

    def test_raw_fence_info_comment_does_not_hide_visible_evidence_labels(self) -> None:
        body = textwrap.dedent(
            """
            - Verified: 2026-07-23
            - Repository: `/repo`
            ```markdown <!--
            - VCS: `git`
            ```
            - VCS: `none`
            - Revision / checkpoint: `none`
            - Identity recheck: `inspection`, 2026-07-23T12:00:00Z, matched none

            | Tool / inspection | Context | Result | Observable evidence |
            |---|---|---|---|
            | `inspection` | `repo` | PASS | Aggregate state inspected. |
            """
        )
        self.assertEqual(["`none`"], sdd_validate.evidence_values(body, "VCS"))
        validator = sdd_validate.Validator(Path("."), Path("."), "historical")
        artifact = sdd_validate.Artifact(Path("plan.md"), "plan.md", {"type": "plan"}, "", "", 1)
        validator._evidence(artifact, "in-progress", "Plan Completion Evidence", 1, body)
        self.assertNotIn("SDD071", {item.code for item in validator.out})

    def test_indented_code_is_not_visible_evidence_or_identity(self) -> None:
        labels = "\n".join(
            f"    {line}"
            for line in (
                "- Verified: 2026-07-23",
                "- Repository: `/repo`",
                "- VCS: `none`",
                "- Revision / checkpoint: `none`",
                "- Identity recheck: `inspection`, 2026-07-23T12:00:00Z, matched none",
            )
        ) + "\n"
        validator = sdd_validate.Validator(Path("."), Path("."), "historical")
        artifact = sdd_validate.Artifact(Path("plan.md"), "plan.md", {"type": "plan"}, "", "", 1)
        validator._evidence(artifact, "complete", "Plan Completion Evidence", 1, labels)
        self.assertIn("SDD071", {item.code for item in validator.out})

        table = "    | Command | Working directory | Result | Observable evidence |\n    |---|---|---|---|\n    | `pytest` | `/repo` | PASS | Fake result. |\n"
        self.assertEqual([], sdd_validate.evidence_rows(table))
        self.assertEqual([], sdd_validate.heading_bodies("    ### Completion Evidence\nproof\n", 3, "Completion Evidence"))

        validator.out.clear()
        validator._completed_identities(
            artifact,
            "### Completed task identities\n    - `1.1`: `checkpoint`\n",
            "Completed task identities",
            {"1.1": "checkpoint"},
            1,
            "task",
        )
        self.assertIn("SDD157", {item.code for item in validator.out})

        for indent in ("", " ", "   "):
            with self.subTest(indent=len(indent)):
                self.assertEqual(
                    ["proof"],
                    sdd_validate.heading_bodies(
                        f"{indent}### Completion Evidence\nproof\n", 3, "Completion Evidence"
                    ),
                )

    def test_tab_and_mixed_indent_cannot_complete_plan_evidence(self) -> None:
        evidence_labels = (
            "- Verified:",
            "- Repository:",
            "- VCS:",
            "- Revision / checkpoint:",
            "- Identity recheck:",
        )
        for name, indent in (("tab", "\t"), ("mixed", " \t")):
            with self.subTest(indent=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.make_valid_tree(root)
                self.complete_phase_and_plan(root)
                plan_path = root / "Plans/Feature/README.md"
                plan = plan_path.read_text(encoding="utf-8")
                for label in evidence_labels:
                    plan = plan.replace(f"\n{label}", f"\n{indent}{label}", 1)
                for line in (
                    "| Command | Working directory | Result | Observable evidence |",
                    "|---|---|---|---|",
                    "| `python3 -m unittest`",
                    "- `1`: ",
                ):
                    plan = plan.replace(f"\n{line}", f"\n{indent}{line}", 1)
                plan_path.write_text(plan, encoding="utf-8")

                findings = self.validate(root)
                codes = {item.code for item in findings if item.path == "Plans/Feature/README.md"}

                self.assertTrue({"SDD071", "SDD072", "SDD158"} <= codes)

    def test_complete_phase_rejects_indented_unchecked_subtasks_and_criteria(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            self.complete_phase_and_plan(root)
            phase_path = root / "Plans/Feature/01-Build.md"
            phase = phase_path.read_text(encoding="utf-8")
            phase = phase.replace("- [x] Implement it.", "  - [ ] Implement it.", 1)
            phase = phase.replace("- [x] AC-01", "   - [ ] AC-01", 1)
            phase_path.write_text(phase, encoding="utf-8")

            findings = self.validate(root)
            messages = {
                item.message
                for item in findings
                if item.path == "Plans/Feature/01-Build.md" and item.code == "SDD069"
            }

            self.assertIn("Complete task `1.1` has unchecked subtasks.", messages)
            self.assertIn("Complete phase has unchecked acceptance criteria.", messages)

        normalized = sdd_validate.normalize_checkboxes(
            "### Subtasks\n   - [x] Retain this item.\n", 3, "Subtasks"
        )
        self.assertIn("   - [ ] Retain this item.", normalized)

    def test_task_rejects_duplicate_visible_subtasks_while_planned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            phase_path = root / "Plans/Feature/01-Build.md"
            phase_path.write_text(
                phase_path.read_text(encoding="utf-8").replace(
                    "### Notes", "### Subtasks\n- [ ] Duplicate subtask.\n### Notes", 1
                ),
                encoding="utf-8",
            )

            findings = self.validate(root)

            self.assertTrue(
                any(
                    item.code == "SDD067"
                    and "Task `1.1` has duplicate visible `### Subtasks` sections." in item.message
                    for item in findings
                )
            )

    def test_committed_completion_rejects_invalid_subtasks_and_criteria_in_a_clean_checkout(self) -> None:
        cases = (
            (
                "task subtask",
                "- [x] Implement it.",
                "  - [ ] Implement it.",
                "Task 1.1 Completion Evidence",
            ),
            (
                "phase criterion",
                "- [x] AC-01",
                "   - [ ] AC-01",
                "Phase Completion Evidence",
            ),
            (
                "duplicate task subtasks",
                "### Notes",
                "### Subtasks\n- [x] Duplicate subtask.\n### Notes",
                "Task 1.1 Completion Evidence",
            ),
        )
        for name, original, replacement, evidence_name in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.make_valid_tree(root)
                self.complete_phase_and_plan(root)
                phase_path = root / "Plans/Feature/01-Build.md"
                phase_path.write_text(
                    phase_path.read_text(encoding="utf-8").replace(original, replacement, 1),
                    encoding="utf-8",
                )
                subprocess.run(["git", "add", "Plans/Feature/01-Build.md"], cwd=root, check=True)
                subprocess.run(
                    ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", f"record unchecked {name}"],
                    cwd=root,
                    check=True,
                    capture_output=True,
                )
                status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=root,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual("", status.stdout)

                findings = self.validate(root)

                self.assertTrue(
                    any(
                        item.code == "SDD072"
                        and evidence_name in item.message
                        and "lifecycle completion is not committed" in item.message
                        for item in findings
                    )
                )

    def test_phase_and_plan_checkpoints_allow_merge_commits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            self.commit_all(root)
            main_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            subprocess.run(["git", "checkout", "-b", "side"], cwd=root, check=True, capture_output=True)
            (root / "side.txt").write_text("side\n", encoding="utf-8")
            subprocess.run(["git", "add", "side.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "side"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            subprocess.run(["git", "checkout", main_branch], cwd=root, check=True, capture_output=True)
            (root / "main.txt").write_text("main\n", encoding="utf-8")
            subprocess.run(["git", "add", "main.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "main"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "merge", "--no-ff", "side", "-m", "phase integration"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            checkpoint = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
            ).stdout.strip()
            validator = sdd_validate.Validator(root, root, "current")
            validator._discover()
            for relative, evidence_name in (
                ("Plans/Feature/01-Build.md", "Phase Completion Evidence"),
                ("Plans/Feature/README.md", "Plan Completion Evidence"),
            ):
                with self.subTest(artifact=relative):
                    validator.out.clear()
                    validator._verify_clean_git_identity(
                        validator.by_path[relative], checkpoint, evidence_name, 1, True
                    )
                    self.assertEqual([], validator.out)

    def test_lifecycle_normalization_preserves_literal_inline_checked_markers(self) -> None:
        source = textwrap.dedent(phase_document()).lstrip().replace(
            "- [ ] Implement it.", "- [x] Implement it with literal inline [x].", 1
        ).replace("- [ ] AC-01", "- [x] AC-01 with literal inline [x]", 1)
        artifact = sdd_validate.Artifact(Path("phase.md"), "phase.md", {"type": "phase"}, "", source, 1)
        normalized = sdd_validate.lifecycle_normalized_artifact(artifact).decode()
        self.assertIn("literal inline [x]", normalized)
        self.assertNotIn("- [x] Implement it", normalized)
        changed = source.replace("literal inline [x]", "literal inline [ ]", 1)
        self.assertNotEqual(
            normalized,
            sdd_validate.lifecycle_normalized_artifact(
                sdd_validate.Artifact(Path("phase.md"), "phase.md", {"type": "phase"}, "", changed, 1)
            ).decode(),
        )

    def test_complete_phase_and_plan_parent_evidence_is_validated_once_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            self.complete_phase_and_plan(root)

            class RecordingValidator(sdd_validate.Validator):
                def __init__(self, *args: object, **kwargs: object) -> None:
                    super().__init__(*args, **kwargs)
                    self.parent_evidence_calls: list[str] = []

                def _evidence(self, artifact: object, status: str, name: str, line: int, body: str) -> None:
                    if name in {"Phase Completion Evidence", "Plan Completion Evidence"}:
                        self.parent_evidence_calls.append(name)
                    super()._evidence(artifact, status, name, line, body)

            validator = RecordingValidator(root, root, "current")
            self.assertEqual([], validator.run())
            self.assertEqual(
                ["Phase Completion Evidence", "Plan Completion Evidence"],
                sorted(validator.parent_evidence_calls),
            )

    def test_complete_phase_and_plan_reject_invalid_parent_evidence_headings_and_labels_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            self.complete_phase_and_plan(root)
            phase_path = root / "Plans/Feature/01-Build.md"
            plan_path = root / "Plans/Feature/README.md"
            phase_source = phase_path.read_text(encoding="utf-8")
            phase_prefix, phase_evidence = phase_source.split(
                "## Phase Completion Evidence\n", 1
            )
            phase_path.write_text(
                phase_prefix
                + "## Phase Completion Evidence\n"
                + phase_evidence.replace("- Verified: 2026-07-24\n", "", 1),
                encoding="utf-8",
            )
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "- Repository:", "- Repository missing:", 1
                ),
                encoding="utf-8",
            )
            findings = sdd_validate.Validator(root, root, "current").run()
            label_errors = {
                item.message
                for item in findings
                if item.code == "SDD071"
            }
            self.assertTrue(any("Phase Completion Evidence" in message for message in label_errors))
            self.assertTrue(any("Plan Completion Evidence" in message for message in label_errors))

            phase_path.write_text(
                phase_path.read_text(encoding="utf-8")
                + "\n## Phase Completion Evidence\nPending — not complete.\n",
                encoding="utf-8",
            )
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "## Plan Completion Evidence", "## Plan Completion Evidence missing", 1
                ),
                encoding="utf-8",
            )
            findings = sdd_validate.Validator(root, root, "current").run()
            heading_errors = [item.message for item in findings if item.code == "SDD020"]
            self.assertTrue(any("Phase Completion Evidence" in message and "duplicated" in message for message in heading_errors))
            self.assertTrue(any("Plan Completion Evidence" in message and "missing" in message for message in heading_errors))

    def test_annotated_tag_objects_are_rejected_for_commit_identities(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            commit = self.commit_all(root)
            subprocess.run(
                ["git", "tag", "-a", "release", "-m", "release"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            tag = subprocess.run(
                ["git", "rev-parse", "release^{tag}"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertFalse(sdd_validate.git_commit_exists(root, tag))
            validator = sdd_validate.Validator(root, root, "historical")
            validator._discover()
            phase = validator.by_path["Plans/Feature/01-Build.md"]
            plan = validator.by_path["Plans/Feature/README.md"]

            validator._verify_clean_git_identity(
                phase, tag, "Task 1.1 Completion Evidence", 1, False
            )
            self.assertIn("SDD072", {item.code for item in validator.out})
            validator.out.clear()
            validator._verify_phase_review_identity(
                phase,
                f"- Revision / checkpoint: `{tag}`\n",
                f"{commit}..{tag}",
                1,
            )
            self.assertIn("SDD173", {item.code for item in validator.out})
            validator.out.clear()
            validator._verify_git_plan_phase_checkpoints(
                plan, [], f"- VCS: `git`\n- Revision / checkpoint: `{tag}`\n", 1
            )
            self.assertIn("SDD175", {item.code for item in validator.out})
            validator.out.clear()
            review = sdd_validate.Artifact(
                root / "Plans/Feature/reviews/01-final.md",
                "Plans/Feature/reviews/01-final.md",
                {"reviewed_planning_revision": tag},
                "",
                "",
                1,
            )
            validator._verify_phase_review_planning_revision(phase, review, 1)
            self.assertIn("SDD174", {item.code for item in validator.out})

    def test_lifecycle_normalized_artifact_normalizes_only_lifecycle_status_paths(self) -> None:
        source = textwrap.dedent(phase_document()).lstrip().replace("status: planned", "status: complete", 1)
        source = source.replace(
            "deliverable: Feature implementation",
            "deliverable: Feature implementation\npolicy:\n  status: retain",
            1,
        ).replace(
            'verification: "Run tests and satisfy FR-01, NFR-01, and AC-01"',
            'verification: "Run tests and satisfy FR-01, NFR-01, and AC-01"\n    policy:\n      status: retain-task',
            1,
        )
        source = source.replace("Pending — not complete.", "recorded evidence", 1)
        artifact = sdd_validate.Artifact(Path("phase.md"), "phase.md", {"type": "phase"}, "", source, 1)
        normalized = sdd_validate.lifecycle_normalized_artifact(artifact).decode()
        self.assertNotIn("status: complete", normalized)
        self.assertIn("status: retain", normalized)
        self.assertIn("status: retain-task", normalized)
        self.assertIn("Pending — not complete.", normalized)
        plan_source = textwrap.dedent(plan_document()).lstrip().replace(
            "status: planned\n    doc: 01-Build.md",
            "status: complete\n    doc: 01-Build.md\n    policy:\n      status: retain-phase",
            1,
        )
        plan = sdd_validate.Artifact(Path("plan.md"), "plan.md", {"type": "plan"}, "", plan_source, 1)
        normalized_plan = sdd_validate.lifecycle_normalized_artifact(plan).decode()
        self.assertNotIn("status: complete", normalized_plan)
        self.assertIn("status: retain-phase", normalized_plan)

    def test_lifecycle_normalization_preserves_frontmatter_bytes_and_rejects_ambiguous_nodes(self) -> None:
        source = (
            "---\r\n"
            "# Preserve this top-level comment.\r\n"
            "title: 'Build' # Preserve title quoting and comment.\r\n"
            "type: phase\r\n"
            'plan: "Feature"\r\n'
            "phase: 1\r\n"
            'status: "complete" # Preserve this lifecycle comment.\r\n'
            "created: 2026-07-21\r\n"
            "updated: '2026-07-24'\r\n"
            "deliverable: Feature implementation\r\n"
            "policy:\r\n"
            "  status: \"retain\"\r\n"
            "tasks:\r\n"
            "  # Preserve this task comment.\r\n"
            "  - id: '1.1'\r\n"
            "    title: \"Implement\"\r\n"
            "    status: 'complete' # Preserve this task lifecycle comment.\r\n"
            "    verification: \"Run tests\"\r\n"
            "    policy:\r\n"
            "      status: 'retain-task'\r\n"
            "---\r\n"
            "# Phase body remains material.\r\n"
            "## 1.1: Implement\r\n"
            "### Completion Evidence\r\n"
            "recorded evidence\r\n"
            "## Phase Completion Evidence\r\n"
            "recorded evidence\r\n"
        )
        artifact = sdd_validate.Artifact(Path("phase.md"), "phase.md", {"type": "phase"}, "", source, 1)
        normalized = sdd_validate.lifecycle_normalized_artifact(artifact).decode()
        for preserved in (
            "# Preserve this top-level comment.\r\n",
            "title: 'Build' # Preserve title quoting and comment.\r\n",
            'plan: "Feature"\r\n',
            "policy:\r\n  status: \"retain\"\r\n",
            "  # Preserve this task comment.\r\n",
            "  - id: '1.1'\r\n",
            "    policy:\r\n      status: 'retain-task'\r\n",
            " # Preserve this lifecycle comment.\r\n",
            "    # Preserve this task lifecycle comment.\r\n",
        ):
            self.assertIn(preserved, normalized)
        self.assertNotIn('status: "complete"', normalized)
        self.assertNotIn("status: 'complete'", normalized)
        self.assertNotIn("updated: '2026-07-24'", normalized)

        lifecycle_only = source.replace('status: "complete"', "status: planned", 1).replace(
            "updated: '2026-07-24'", "updated: 2026-07-21", 1
        ).replace("status: 'complete'", "status: planned", 1)
        self.assertEqual(
            normalized,
            sdd_validate.lifecycle_normalized_artifact(
                sdd_validate.Artifact(Path("phase.md"), "phase.md", {"type": "phase"}, "", lifecycle_only, 1)
            ).decode(),
        )
        for material_change in (
            source.replace("title: 'Build'", 'title: "Build"', 1),
            source.replace("# Preserve this top-level comment.", "# Changed comment."),
            source.replace("created: 2026-07-21", "created:    2026-07-21", 1),
            source.replace("status: 'retain-task'", "status: changed", 1),
        ):
            self.assertNotEqual(
                normalized,
                sdd_validate.lifecycle_normalized_artifact(
                    sdd_validate.Artifact(Path("phase.md"), "phase.md", {"type": "phase"}, "", material_change, 1)
                ).decode(),
            )

        for kind, malformed in (
            (
                "phase",
                "---\ntype: phase\nstatus: complete\ntasks: [{id: '1.1', status: complete}]\n---\n",
            ),
            (
                "plan",
                "---\ntype: plan\nstatus: complete\nphases: [{id: 1, status: complete}]\n---\n",
            ),
            ("phase", "---\ntype: phase\nstatus: |\n  complete\n---\n"),
        ):
            with self.assertRaisesRegex(ValueError, "unsupported flow or multiline lifecycle node"):
                sdd_validate.lifecycle_normalized_artifact(
                    sdd_validate.Artifact(Path(f"{kind}.md"), f"{kind}.md", {"type": kind}, "", malformed, 1)
                )

    def test_visible_legacy_evidence_rollups_are_rejected_before_pending_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            plan_path = root / "Plans/Feature/README.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8")
                + "\n### Phase 1 Evidence Rollup\nLegacy proof.\n",
                encoding="utf-8",
            )
            phase_path = root / "Plans/Feature/01-Build.md"
            phase_path.write_text(
                phase_path.read_text(encoding="utf-8")
                + "\n### Task 1.1 Evidence Rollup\nLegacy proof.\n",
                encoding="utf-8",
            )
            findings = self.validate(root)
            codes_by_path = {
                item.path: item.code
                for item in findings
                if "Evidence Rollup" in item.message
            }
            self.assertEqual("SDD158", codes_by_path["Plans/Feature/README.md"])
            self.assertEqual("SDD157", codes_by_path["Plans/Feature/01-Build.md"])

        for status in ("planned", "in-progress", "complete"):
            validator = sdd_validate.Validator(Path("."), Path("."))
            artifact = sdd_validate.Artifact(
                Path("phase.md"),
                "phase.md",
                {"type": "phase", "status": status},
                "## Phase Completion Evidence\nPending — not complete.\n### Task 1.1 Evidence Rollup\nLegacy proof.\n",
                "",
                1,
            )
            validator._headings(artifact)
            self.assertIn("SDD157", {item.code for item in validator.out})

    def test_visible_legacy_evidence_rollup_atx_h3_variants_are_rejected(self) -> None:
        headings = (
            "   ### Task 1.1 Evidence Rollup",
            "### Task 1.1 Evidence Rollup ###   ",
            "### tAsK 1.1 eViDeNcE rOlLuP",
        )
        for heading in headings:
            with self.subTest(heading=heading), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.make_valid_tree(root)
                phase_path = root / "Plans/Feature/01-Build.md"
                phase_path.write_text(
                    phase_path.read_text(encoding="utf-8")
                    + "\n<!--\n### Task 1.1 Evidence Rollup\n-->\n"
                    + "```markdown\n### Task 1.1 Evidence Rollup\n```\n"
                    + f"{heading}\nLegacy proof.\n",
                    encoding="utf-8",
                )

                findings = self.validate(root)

                self.assertTrue(
                    any(
                        item.code == "SDD157"
                        and item.path == "Plans/Feature/01-Build.md"
                        for item in findings
                    )
                )

    def test_task_evidence_lifecycle_normalization_rejects_extraneous_headings(self) -> None:
        source = textwrap.dedent(phase_document()).lstrip().replace(
            "## Overview\nBuild it according to FR-01 and NFR-01.",
            "## Overview\n### Completion Evidence\nPost-review policy must remain material.\nBuild it according to FR-01 and NFR-01.",
        )
        artifact = sdd_validate.Artifact(Path("phase.md"), "phase.md", {"type": "phase"}, "", source, 1)
        normalized = sdd_validate.lifecycle_normalized_artifact(artifact).decode()
        self.assertIn("Post-review policy must remain material.", normalized)

        changed = source.replace(
            "Post-review policy must remain material.", "Post-review policy changed after review."
        )
        changed_artifact = sdd_validate.Artifact(Path("phase.md"), "phase.md", {"type": "phase"}, "", changed, 1)
        self.assertNotEqual(
            normalized,
            sdd_validate.lifecycle_normalized_artifact(changed_artifact).decode(),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_valid_tree(root)
            write(root, "Plans/Feature/01-Build.md", source)
            findings = self.validate(root)
            self.assertTrue(any(item.code == "SDD067" and "outside" in item.message for item in findings))

            duplicate = source.replace(
                "Pending — not complete.\n## Acceptance Criteria",
                "Pending — not complete.\n### Completion Evidence\nDuplicate task evidence.\n## Acceptance Criteria",
                1,
            )
            write(root, "Plans/Feature/01-Build.md", duplicate)
            findings = self.validate(root)
            self.assertTrue(any(item.code == "SDD067" and "duplicate" in item.message for item in findings))


if __name__ == "__main__":
    unittest.main()
