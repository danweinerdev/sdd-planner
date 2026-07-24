import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IDENTIFIER = "implement_task"


class ImplementationDispatchTests(unittest.TestCase):
    def test_identifier_is_documented_at_all_implementation_dispatch_points(self):
        files = (
            ROOT / "skills" / "sdd-implement" / "SKILL.md",
            ROOT / "skills" / "sdd-plan" / "SKILL.md",
            ROOT / "shared" / "agent-runtime.md",
            ROOT / "README.md",
        )
        for path in files:
            self.assertIn(IDENTIFIER, path.read_text(encoding="utf-8"), path)

    def test_implementation_dispatch_instructions_are_complete_and_neutral(self):
        implement = (ROOT / "skills" / "sdd-implement" / "SKILL.md").read_text(
            encoding="utf-8"
        ).lower()
        rehearsal = (ROOT / "skills" / "sdd-plan" / "SKILL.md").read_text(
            encoding="utf-8"
        ).lower()
        for text in (implement, rehearsal):
            for required in (
                "implement_task",
                "target paths",
                "acceptance criteria",
                "trap",
                "accepted-decision statements",
                "verification requirements",
                "primary agent",
            ):
                self.assertIn(required, text)
            self.assertRegex(text, r"(?:exactly one|one exact) plan task")
            for forbidden in ("subagent_type", "openai/", "anthropic/", "gpt-", "claude-"):
                self.assertNotIn(forbidden, text)
        self.assertIn("do not request an agent", implement)
        self.assertIn("without requesting an agent", rehearsal)

    def test_decision_d_0009_governs_the_contract(self):
        decisions = (ROOT / "Decisions" / "decisions.md").read_text(encoding="utf-8")
        self.assertIn("id: D-0009", decisions)
        self.assertIn("status: accepted", decisions)
        self.assertIn("stable runtime-neutral identifier implement_task", decisions)
        self.assertIn("sdd-implement emits implement_task", decisions)

    def test_task_boundaries_are_atomic_reviewed_native_scm_revisions(self):
        plan = (ROOT / "skills" / "sdd-plan" / "SKILL.md").read_text(
            encoding="utf-8"
        ).lower()
        implement = (ROOT / "skills" / "sdd-implement" / "SKILL.md").read_text(
            encoding="utf-8"
        ).lower()
        reviewer = (
            ROOT / "shared" / "agent-prompts" / "plan-reviewer.md"
        ).read_text(encoding="utf-8").lower()
        phase_template = (
            ROOT / "shared" / "templates" / "plan-phase.md"
        ).read_text(encoding="utf-8").lower()

        for text in (plan, implement, reviewer, phase_template):
            for required in ("clean", "complete", "bisectable"):
                self.assertIn(required, text)
        self.assertIn("native-scm revision boundaries", plan)
        self.assertIn("split\n  and reorder", plan)
        self.assertIn("subtasks stay inside the boundary", plan)
        self.assertIn("focused\n   code review", implement)
        self.assertIn("complete\n   state", implement)
        self.assertIn("git adapter", implement)
        self.assertIn("scoped implementation commit", implement)
        self.assertIn("scoped lifecycle commit", implement)
        self.assertNotIn("commit only when the user or repository policy", implement)

    def test_native_scm_completion_does_not_generate_synthetic_source_identity(self):
        contract = (ROOT / "shared" / "completion-evidence.md").read_text(
            encoding="utf-8"
        ).lower()
        implement = (ROOT / "skills" / "sdd-implement" / "SKILL.md").read_text(
            encoding="utf-8"
        ).lower()
        self.assertIn("native scm completion", contract)
        self.assertIn("native scm is the sole durable source identity", contract)
        self.assertIn("dirty git, no-scm", contract)
        self.assertIn("do not invent a fallback source identity", implement)
        self.assertNotIn("content snapshot", contract)
        self.assertNotIn("governing intent", contract)

    def test_decisions_govern_atomic_reviewed_task_boundaries(self):
        decisions = (ROOT / "Decisions" / "decisions.md").read_text(encoding="utf-8")
        self.assertIn("id: D-0018", decisions)
        self.assertIn("id: D-0016", decisions)
        self.assertIn("id: D-0017", decisions)
        self.assertIn("id: D-0014", decisions)
        self.assertIn("id: D-0015", decisions)
        self.assertIn("clean, complete, and independently bisectable", decisions)

    def test_graph_aware_scope_decision_is_recorded(self):
        decisions = (ROOT / "Decisions" / "decisions.md").read_text(encoding="utf-8")
        self.assertIn("id: D-0013", decisions)
        self.assertIn("transitive explicit related links", decisions)


if __name__ == "__main__":
    unittest.main()
