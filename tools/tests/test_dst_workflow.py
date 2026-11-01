import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import dst_workflow as workflow


class WorkflowTests(unittest.TestCase):
    def test_old_or_failed_assertions_cannot_pass(self):
        log = "[DSTWF:abcd:ASSERT:PASS] feature\n[DSTWF:abcd:ASSERT:FAIL] feature\n[DSTWF:abcd:ASSERT:PASS] feature"
        self.assertEqual(workflow.collect_assertions(log, "abcd"), {"feature": False})
        self.assertEqual(workflow.collect_assertions(log, "ffff"), {})

    def test_incomplete_plan_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / "plan.json"
            for requirements in ([], [{"id": "a", "description": "需求", "stage": "server", "assertions": []}],
                                 [{"id": "a", "description": "需求", "stage": "manual", "assertions": ["a"]}]):
                workflow.write_json(plan, {"schema_version": 1, "mod": "mod", "requirements": requirements})
                with self.assertRaises(ValueError):
                    workflow.load_plan(plan, root / "mod")

    def test_cleanup_cannot_remove_parent_or_other_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            protected = parent / "user"
            protected.mkdir()
            for target, name in ((parent, parent.name), (protected, "other")):
                with self.assertRaises(ValueError):
                    workflow.remove_owned(target, parent, name)
            self.assertTrue(protected.exists())

    def test_runtime_json_and_tests_are_fingerprinted(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = Path(tmp)
            (mod / "config.json").write_text('{"damage":1}')
            (mod / "dst_selftest.lua").write_text('return function(t) end')
            first = workflow.source_manifest(mod)
            self.assertIn("dst_selftest.lua", first)
            (mod / "config.json").write_text('{"damage":2}')
            self.assertNotEqual(first, workflow.source_manifest(mod))

    def test_apply_requires_complete_current_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "evidence"
            evidence.mkdir()
            config = {"evidence_root": str(evidence)}
            for report in ({"status": "passed", "command": "test"},
                           {"status": "blocked", "command": "verify"}):
                path = evidence / "result.json"
                workflow.write_json(path, report)
                with self.assertRaises(ValueError):
                    workflow.require_verified(config, root / "mod", str(path))

    def test_static_failure_stops_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / "plan.json"
            workflow.write_json(plan, {"schema_version": 1, "mod": "mod", "requirements": [
                {"id": "a", "description": "需求", "stage": "server", "assertions": ["a"]}]})
            with patch.object(workflow, "static_check", return_value={"status": "failed"}), patch.object(workflow, "server_test") as server:
                result = workflow.verify({}, root / "mod", root, plan, 5)
            self.assertEqual(result["status"], "failed")
            server.assert_not_called()


if __name__ == "__main__":
    unittest.main()
