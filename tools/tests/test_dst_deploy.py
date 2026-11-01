"""在临时目录验证部署边界、过滤、残留清理与失败恢复，不触碰真实游戏。"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dst_deploy


class DeployTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dst-deploy-test-")
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.game = self.root / "game"
        self.evidence = self.root / "evidence"
        self.source = self.workspace / "sample-mod"
        self.target = self.game / "mods" / "sample-mod"
        self.source.mkdir(parents=True)
        self.target.parent.mkdir(parents=True)
        self.write(self.source, "modinfo.lua", 'name = "sample"')
        self.write(self.source, "modmain.lua", "-- new")

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def write(root, relative, content):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def deploy(self, **kwargs):
        return dst_deploy.deploy_mod(self.workspace, self.game, "sample-mod", self.evidence, **kwargs)

    def test_preview_filters_development_files_and_preserves_png(self):
        for name in ("README.md", "dst_selftest.lua", "selftest-runtime-report.json", "tests/test.lua", "logs/server_log.txt", ".git/config", "art/source.psd"):
            self.write(self.source, name, "development")
        self.write(self.source, "images/icon.png", "runtime image")
        self.write(self.target, "old.lua", "old")
        result = self.deploy()
        self.assertEqual(result["status"], "preview")
        self.assertEqual(result["changes"]["add"], ["images/icon.png", "modinfo.lua", "modmain.lua"])
        self.assertEqual(result["changes"]["delete"], ["old.lua"])
        self.assertFalse(self.evidence.exists())
        self.assertTrue((self.target / "old.lua").exists())

    def test_apply_removes_renamed_file_backs_up_and_verifies(self):
        self.write(self.target, "old.lua", "old code")
        self.write(self.target, "modmain.lua", "-- old")
        self.write(self.source, "renamed.lua", "new code")
        other = self.target.parent / "workshop-123" / "modmain.lua"
        self.write(other.parent, other.name, "other mod")
        result = self.deploy(apply=True)
        self.assertEqual(result["status"], "applied")
        self.assertTrue(result["hash_verify"])
        backup = Path(result["backup_dir"])
        self.assertEqual((backup / "before" / "old.lua").read_text(), "old code")
        self.assertEqual((backup / "before" / "modmain.lua").read_text(), "-- old")
        self.assertFalse((self.target / "old.lua").exists())
        self.assertEqual(other.read_text(), "other mod")
        self.assertEqual(dst_deploy._inventory(self.target), result["expected"])
        self.assertEqual(json.loads((backup / "manifest.json").read_text(encoding="utf-8"))["status"], "applied")
        again = self.deploy(apply=True)
        self.assertEqual(again["status"], "unchanged")
        self.assertIsNone(again["backup_dir"])

    def test_refuses_wrong_names_and_overlapping_roots(self):
        for mod in ("..", "../sample-mod", "sample-mod/child", "workshop-123", "unknown"):
            with self.subTest(mod=mod), self.assertRaises(dst_deploy.DeployError):
                dst_deploy.plan_deploy(self.workspace, self.game, mod, self.evidence)
        with self.assertRaises(dst_deploy.DeployError):
            dst_deploy.plan_deploy(self.workspace, self.workspace, "sample-mod", self.evidence)
        with self.assertRaises(dst_deploy.DeployError):
            dst_deploy.plan_deploy(self.workspace, self.game, "sample-mod", self.workspace / "reports")
        self.assertFalse(self.evidence.exists())

    def test_refuses_directory_links_in_source_or_target(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.write(outside, "private.txt", "must stay")
        for base in (self.source, self.target):
            base.mkdir(exist_ok=True)
            link = base / "linked"
            try:
                try:
                    link.symlink_to(outside, target_is_directory=True)
                except OSError:
                    if os.name != "nt":
                        raise
                    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
                    if result.returncode:
                        self.skipTest("系统不允许创建用于验证的符号链接或目录联接")
                with self.assertRaises(dst_deploy.DeployError):
                    self.deploy(apply=True)
                self.assertEqual((outside / "private.txt").read_text(), "must stay")
            finally:
                if os.path.lexists(link):
                    if link.is_symlink():
                        link.unlink()
                    else:
                        link.rmdir()
        self.assertFalse(self.evidence.exists())

    def test_failed_copy_restores_deleted_updated_and_added_files(self):
        self.write(self.target, "old.lua", "old")
        self.write(self.target, "modmain.lua", "-- old")
        self.write(self.source, "scripts/added.lua", "added")
        previous = dst_deploy._inventory(self.target)
        real_copy = shutil.copy2
        failed = False

        def copy(src, dst, *args, **kwargs):
            nonlocal failed
            if Path(dst) == self.target / "modmain.lua" and not failed:
                failed = True
                raise OSError("simulated write failure")
            return real_copy(src, dst, *args, **kwargs)

        with patch.object(dst_deploy.shutil, "copy2", side_effect=copy):
            with self.assertRaisesRegex(dst_deploy.DeployError, "rolled_back"):
                self.deploy(apply=True)
        self.assertTrue(failed)
        self.assertEqual(dst_deploy._inventory(self.target), previous)
        self.assertFalse((self.target / "scripts").exists())
        manifest = next(self.evidence.glob("deploy/*/manifest.json"))
        self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["status"], "rolled_back")

    def test_unreadable_source_directory_aborts_instead_of_deleting_target(self):
        self.write(self.source, "scripts/keep.lua", "keep")
        self.write(self.target, "scripts/keep.lua", "keep")
        real_scandir = os.scandir

        def scandir(path):
            if Path(path) == self.source / "scripts":
                raise PermissionError("simulated unreadable directory")
            return real_scandir(path)

        with patch.object(dst_deploy.os, "scandir", side_effect=scandir):
            with self.assertRaises(PermissionError):
                self.deploy(apply=True)
        self.assertEqual((self.target / "scripts/keep.lua").read_text(), "keep")
        self.assertFalse(self.evidence.exists())

    def test_refuses_hardlinked_target_file(self):
        self.target.mkdir()
        outside = self.root / "outside.lua"
        outside.write_text("outside")
        os.link(outside, self.target / "modmain.lua")
        with self.assertRaises(dst_deploy.DeployError):
            self.deploy(apply=True)
        self.assertEqual(outside.read_text(), "outside")
        self.assertFalse(self.evidence.exists())

    def test_post_copy_hash_mismatch_triggers_rollback(self):
        self.write(self.target, "modmain.lua", "-- old")
        previous = dst_deploy._inventory(self.target)
        real_copy = shutil.copy2
        corrupted = False

        def copy(src, dst, *args, **kwargs):
            nonlocal corrupted
            result = real_copy(src, dst, *args, **kwargs)
            if Path(dst) == self.target / "modmain.lua" and not corrupted:
                Path(dst).write_text("unexpected content")
                corrupted = True
            return result

        with patch.object(dst_deploy.shutil, "copy2", side_effect=copy):
            with self.assertRaisesRegex(dst_deploy.DeployError, "rolled_back"):
                self.deploy(apply=True)
        self.assertEqual(dst_deploy._inventory(self.target), previous)

    def test_failed_final_manifest_restores_original_files(self):
        self.write(self.target, "modmain.lua", "-- old")
        previous = dst_deploy._inventory(self.target)
        real_save = dst_deploy._save_manifest

        def save(backup, manifest):
            if manifest["status"] == "applied":
                raise OSError("simulated evidence disk failure")
            return real_save(backup, manifest)

        with patch.object(dst_deploy, "_save_manifest", side_effect=save):
            with self.assertRaisesRegex(dst_deploy.DeployError, "rolled_back"):
                self.deploy(apply=True)
        self.assertEqual(dst_deploy._inventory(self.target), previous)

    def test_file_can_be_replaced_with_directory_and_back(self):
        self.write(self.target, "scripts", "old file")
        self.write(self.source, "scripts/new.lua", "new")
        self.deploy(apply=True)
        self.assertTrue((self.target / "scripts" / "new.lua").is_file())
        (self.source / "scripts" / "new.lua").unlink()
        (self.source / "scripts").rmdir()
        self.write(self.source, "scripts", "new file")
        self.deploy(apply=True)
        self.assertEqual((self.target / "scripts").read_text(), "new file")


if __name__ == "__main__":
    unittest.main()
