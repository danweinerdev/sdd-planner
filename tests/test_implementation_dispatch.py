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


if __name__ == "__main__":
    unittest.main()
