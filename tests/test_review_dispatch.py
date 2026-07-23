import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISPATCH_IDS = (
    "review_plan_drift",
    "review_quality",
    "review_spec_compliance",
    "review_blind_spots",
)
MAPPING = {
    "Plan drift": "review_plan_drift",
    "Quality": "review_quality",
    "Spec compliance": "review_spec_compliance",
    "Blind spots": "review_blind_spots",
}


class ReviewDispatchTests(unittest.TestCase):
    def test_skill_and_shared_contract_expose_every_dispatch_identifier(self):
        skill = (ROOT / "skills" / "sdd-code-review" / "SKILL.md").read_text()
        shared = (ROOT / "shared" / "review-lanes.md").read_text()
        for lens, identifier in MAPPING.items():
            pattern = rf"\| {re.escape(lens)} \| `{re.escape(identifier)}` \|"
            self.assertRegex(skill, pattern)
            self.assertRegex(shared, pattern)
        self.assertIn("task name or description field", skill)

    def test_isolation_fallback_requires_accurate_review_mode(self):
        skill = (ROOT / "skills" / "sdd-code-review" / "SKILL.md").read_text()
        self.assertIn("fresh-context isolation is unavailable", skill)
        self.assertIn("label the review **mixed**", skill)
        self.assertIn("label it **single-agent review**", skill)

    def test_dispatch_contract_remains_runtime_neutral(self):
        skill = (ROOT / "skills" / "sdd-code-review" / "SKILL.md").read_text().lower()
        shared = (ROOT / "shared" / "review-lanes.md").read_text().lower()
        for forbidden in ("subagent_type", "gpt-", "claude-", "anthropic/"):
            self.assertNotIn(forbidden, skill)
            self.assertNotIn(forbidden, shared)

    def test_phase_completion_requires_persisted_frozen_aligned_four_lane_review(self):
        skill = (ROOT / "skills" / "sdd-code-review" / "SKILL.md").read_text()
        evidence = (ROOT / "shared" / "completion-evidence.md").read_text()
        artifacts = (ROOT / "shared" / "review-artifacts.md").read_text()
        validator = (ROOT / "scripts" / "sdd_validate.py").read_text()
        for text in (skill, evidence, artifacts):
            for required in (
                "frozen",
                "Aligned",
                "Needs changes",
                "Blocked",
                "all four",
                "material",
            ):
                self.assertIn(required, text)
        for identifier in DISPATCH_IDS:
            self.assertIn(identifier, artifacts)
        for required in ("review_mode", "lane_results", "reviewed_identity", "PASS/Aligned"):
            self.assertIn(required, artifacts)
            self.assertIn(required, validator)
        self.assertIn("Final aligned review", validator)
        self.assertIn("SDD166", validator)
        self.assertIn("SDD167", validator)
        self.assertIn("SDD172", validator)

    def test_manifest_version_is_semver(self):
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
