import tempfile
import unittest
import json
from pathlib import Path
from scripts.validate_workflow_output import ContractError, validate_fanout, validate_literature

class WorkflowContractTests(unittest.TestCase):
    def test_literature_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "literature.md"
            headings = ("Paper Positioning", "Key References (from paper)", "Related Work (IEEE search)", "Author Background", "Research Landscape Summary")
            path.write_text("# Literature Context\n" + "\n".join(f"## {h}\ncontent" for h in headings), encoding="utf-8")
            validate_literature(path)
            path.write_text("## Paper Positioning\nx", encoding="utf-8")
            with self.assertRaises(ContractError): validate_literature(path)

    def test_fanout_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            path = directory / "novelty.md"
            path.write_text("## 1 · Claim\n- Evidence: Intro\n- Severity: major\n- Suggested action: Compare.\n", encoding="utf-8")
            validate_fanout(directory, ["novelty"])
            path.write_text("## 1 · Claim\n- Evidence: Intro\n", encoding="utf-8")
            with self.assertRaises(ContractError): validate_fanout(directory, ["novelty"])
            with self.assertRaises(ContractError): validate_fanout(directory, ["missing"])

    def test_fanout_rejects_extra_stale_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            valid = "## 1 · Claim\n- Evidence: Intro\n- Severity: minor\n- Suggested action: Clarify.\n"
            (directory / "novelty.md").write_text(valid, encoding="utf-8")
            (directory / "stale.md").write_text(valid, encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "unexpected/stale"):
                validate_fanout(directory, ["novelty"])

    def test_partial_subset_requires_exact_approval_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "novelty.md").write_text(
                "## 1 · Claim\n- Evidence: Intro\n- Severity: major\n- Suggested action: Compare.\n", encoding="utf-8")
            approval = directory.parent / "fanout-approved.json"
            approval.write_text(json.dumps({"user_approved": True, "approved_angles": ["novelty"], "skipped_angles": ["methodology"]}), encoding="utf-8")
            validate_fanout(directory, ["novelty"], approval)
            approval.write_text(json.dumps({"user_approved": True, "approved_angles": ["methodology"], "skipped_angles": ["novelty"]}), encoding="utf-8")
            with self.assertRaises(ContractError): validate_fanout(directory, ["novelty"], approval)

if __name__ == "__main__": unittest.main()
