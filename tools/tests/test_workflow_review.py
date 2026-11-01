"""独立审查发现的验收边界回归；只操作临时目录，不启动饥荒。"""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dst_workflow
from dst_static import check_resources


class WorkflowReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dst-workflow-review-")
        self.root = Path(self.temp.name)
        self.mod = self.root / "workspace" / "mod"
        self.mod.mkdir(parents=True)
        self.dst = self.root / "game"
        archive = self.dst / "data/databundles/scripts.zip"
        archive.parent.mkdir(parents=True)
        with zipfile.ZipFile(archive, "w") as stream:
            stream.writestr("scripts/mods.lua", "MOD_API_VERSION = 10")
        (self.mod / "modmain.lua").write_text("-- no resources")

    def tearDown(self):
        self.temp.cleanup()

    def test_runtime_json_and_text_changes_invalidate_manifest(self):
        settings = self.mod / "settings.json"
        text = self.mod / "dialogue.txt"
        settings.write_text('{"damage": 1}')
        text.write_text("first dialogue")
        before = dst_workflow.source_manifest(self.mod)
        settings.write_text('{"damage": 2}')
        self.assertNotEqual(before, dst_workflow.source_manifest(self.mod))
        before = dst_workflow.source_manifest(self.mod)
        text.write_text("second dialogue")
        self.assertNotEqual(before, dst_workflow.source_manifest(self.mod))

    def test_directory_link_is_refused(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "private.lua").write_text("-- do not follow")
        link = self.mod / "external"
        try:
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                if os.name != "nt":
                    raise
                process = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
                if process.returncode:
                    self.skipTest("当前系统不允许创建测试目录联接")
            with self.assertRaises(ValueError):
                dst_workflow.regular_tree(self.mod)
            self.assertEqual((outside / "private.lua").read_text(), "-- do not follow")
        finally:
            if os.path.lexists(link):
                if link.is_symlink():
                    link.unlink()
                else:
                    link.rmdir()

    def test_invalid_metadata_literal_cannot_pass(self):
        (self.mod / "modinfo.lua").write_text(
            "name=nil\ndescription=false\nauthor=1\nversion={}\n"
            "api_version=10\ndst_compatible=true\n"
        )
        self.assertEqual(check_resources(self.mod, self.dst)["status"], "failed")

    def test_valid_metadata_literals_pass(self):
        (self.mod / "modinfo.lua").write_text(
            'name="sample"\ndescription="sample mod"\nauthor="local"\nversion="1.0.0"\n'
            "api_version=10\ndst_compatible=true\n"
        )
        self.assertEqual(check_resources(self.mod, self.dst)["status"], "passed")

    def test_assertion_failure_cannot_be_overwritten_or_replaced_by_old_run(self):
        current, old = "a" * 32, "b" * 32
        text = (
            f"[DSTWF:{current}:ASSERT:FAIL] requirement\n"
            f"[DSTWF:{current}:ASSERT:PASS] requirement\n"
            f"[DSTWF:{old}:ASSERT:PASS] missing_requirement\n"
        )
        self.assertEqual(dst_workflow.collect_assertions(text, current), {"requirement": False})

    def verified_fixture(self):
        """生成具备全部绑定项的成功报告，随后只调用部署的纯校验门禁。"""
        workspace = self.mod.parent
        config = {
            "workspace": str(workspace), "dst_root": str(self.dst),
            "evidence_root": str(self.root / "evidence"),
            "upstream_root": str(self.root / "upstream"),
            "expected_upstream_commit": dst_workflow.PIN,
            "python": sys.executable,
        }
        (self.mod / "modinfo.lua").write_text(
            'name="sample"\ndescription="sample mod"\nauthor="local"\nversion="1"\n'
            'api_version=10\ndst_compatible=true\n'
        )
        script = workspace / "tools/scenarios/mod.lua"
        script.parent.mkdir(parents=True)
        script.write_text('TEST.Assert("example", true)\nTEST.Done()\n')
        requirements = [{"id": "baseline", "description": "示例验收", "stage": "server", "assertions": ["example"]}]
        plan = workspace / "tools/acceptance/mod.json"
        dst_workflow.write_json(plan, {
            "schema_version": 1, "mod": "mod", "requirements": requirements,
            "server_script": "tools/scenarios/mod.lua",
        })
        tool_hashes = {"dst_workflow.py": "a" * 64, "dst_deploy.py": "b" * 64}
        report = {
            "command": "verify", "status": "passed", "mod": str(self.mod),
            "source_sha256": dst_workflow.source_manifest(self.mod),
            "scripts_zip_sha256": dst_workflow.sha(self.dst / "data/databundles/scripts.zip"),
            "upstream_commit": dst_workflow.PIN,
            "plan": str(plan), "plan_sha256": dst_workflow.sha(plan),
            "scenario_sha256": {str(script): dst_workflow.sha(script)},
            "tool_sha256": tool_hashes,
            "requirements": requirements,
            "stages": {
                "check": {"status": "passed"},
                "server": {"status": "passed", "assertions": {"example": True}, "cleanup": {"passed": True, "errors": []}},
            },
        }
        evidence = Path(config["evidence_root"]) / "run" / "result.json"
        dst_workflow.write_json(evidence, report)
        return config, evidence, report, plan, script, tool_hashes

    def test_matching_complete_verify_report_is_accepted(self):
        config, evidence, report, _, _, tools = self.verified_fixture()
        with patch.object(dst_workflow, "tool_manifest", return_value=tools):
            self.assertEqual(dst_workflow.require_verified(config, self.mod, evidence), report)

    def test_changed_runtime_file_invalidates_verify_report(self):
        config, evidence, report, _, _, tools = self.verified_fixture()
        with patch.object(dst_workflow, "tool_manifest", return_value=tools):
            self.assertEqual(dst_workflow.require_verified(config, self.mod, evidence), report)
            (self.mod / "modmain.lua").write_text("-- changed behavior")
            with self.assertRaisesRegex(ValueError, "源码已变化"):
                dst_workflow.require_verified(config, self.mod, evidence)

    def test_changed_game_zip_invalidates_verify_report(self):
        config, evidence, report, _, _, tools = self.verified_fixture()
        with patch.object(dst_workflow, "tool_manifest", return_value=tools):
            self.assertEqual(dst_workflow.require_verified(config, self.mod, evidence), report)
            with zipfile.ZipFile(self.dst / "data/databundles/scripts.zip", "w") as stream:
                stream.writestr("scripts/mods.lua", "MOD_API_VERSION = 11")
            with self.assertRaisesRegex(ValueError, "游戏版本已变化"):
                dst_workflow.require_verified(config, self.mod, evidence)

    def test_changed_plan_invalidates_verify_report(self):
        config, evidence, report, plan, _, tools = self.verified_fixture()
        with patch.object(dst_workflow, "tool_manifest", return_value=tools):
            self.assertEqual(dst_workflow.require_verified(config, self.mod, evidence), report)
            changed = dst_workflow.read_json(plan)
            changed["requirements"][0]["assertions"].append("additional")
            dst_workflow.write_json(plan, changed)
            with self.assertRaisesRegex(ValueError, "验收标准已变化"):
                dst_workflow.require_verified(config, self.mod, evidence)

    def test_changed_scenario_invalidates_verify_report(self):
        config, evidence, report, _, script, tools = self.verified_fixture()
        with patch.object(dst_workflow, "tool_manifest", return_value=tools):
            self.assertEqual(dst_workflow.require_verified(config, self.mod, evidence), report)
            script.write_text('TEST.Assert("example", false)\nTEST.Done()\n')
            with self.assertRaisesRegex(ValueError, "验收脚本已变化"):
                dst_workflow.require_verified(config, self.mod, evidence)

    def test_changed_local_tools_invalidate_verify_report(self):
        config, evidence, report, _, _, tools = self.verified_fixture()
        with patch.object(dst_workflow, "tool_manifest", return_value=tools) as manifest:
            self.assertEqual(dst_workflow.require_verified(config, self.mod, evidence), report)
            manifest.return_value = {**tools, "dst_workflow.py": "c" * 64}
            with self.assertRaisesRegex(ValueError, "本地测试工具已变化"):
                dst_workflow.require_verified(config, self.mod, evidence)

    def test_changed_upstream_commit_invalidates_verify_report(self):
        config, evidence, report, _, _, tools = self.verified_fixture()
        with patch.object(dst_workflow, "tool_manifest", return_value=tools):
            self.assertEqual(dst_workflow.require_verified(config, self.mod, evidence), report)
            config["expected_upstream_commit"] = "d" * 40
            with self.assertRaisesRegex(ValueError, "测试工具版本已变化"):
                dst_workflow.require_verified(config, self.mod, evidence)


if __name__ == "__main__":
    unittest.main()
