"""客户端证据门禁与进程归属回归，不启动游戏。"""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

SPEC = importlib.util.spec_from_file_location("dst_client_probe", Path(__file__).parents[1] / "dst_client_probe.py")
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)
sys.path.insert(0, str(Path(__file__).parents[1]))
import dst_workflow


class ClientProbeTests(unittest.TestCase):
    token = "audit_123456"

    def line(self, event, **fields):
        return f"[DST_CLIENT:{self.token}] " + json.dumps({"side": "client", "event": event, **fields})

    def complete(self):
        return "\n".join([*(self.line(e) for e in probe.REQUIRED_EVENTS), self.line("assert", name="hud", ok=True)])

    def test_server_or_old_marker_cannot_pass(self):
        self.assertFalse(probe.read_client_evidence("[DME:x:DONE]\n" + self.complete().replace(self.token, "old_token"), self.token)["passed"])

    def test_requires_hud_replica_and_assertions(self):
        self.assertTrue(probe.read_client_evidence(self.complete(), self.token)["passed"])
        for event in probe.REQUIRED_EVENTS:
            lines = [line for line in self.complete().splitlines() if f'"event": "{event}"' not in line]
            self.assertFalse(probe.read_client_evidence("\n".join(lines), self.token)["passed"])

    def test_late_false_assert_overrides_done(self):
        result = probe.read_client_evidence(self.complete() + "\n" + self.line("assert", name="replica", ok=False), self.token)
        self.assertFalse(result["passed"])
        self.assertEqual(result["failures"], ["replica"])

    def test_role_ownership_blocker_cannot_pass(self):
        result = probe.read_client_evidence(self.complete()+"\n"+self.line("blocked", details="not_owned"),self.token)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blockers"], ["not_owned"])

    def test_inventory_cache_requires_exact_account_and_preserves_signed_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, target = root / "source", root / "target"
            source.mkdir()
            content = b'{"OfflineUserID":"OU_fixture","Items":[]}'
            (source / "inventory_cache_prod").write_bytes(content)
            (source / "inventory_cache_prod_sig").write_bytes(b'fixture-signature')
            (source / "login_token").write_text("must-not-copy")
            denied = probe.copy_inventory_cache(source, target, "OU_other")
            self.assertEqual(denied["status"], "unavailable")
            self.assertFalse(target.exists())
            result = probe.copy_inventory_cache(source, target, "OU_fixture")
            self.assertEqual(result["status"], "copied_for_engine_validation")
            self.assertEqual((target / "inventory_cache_prod").read_bytes(),content)
            self.assertEqual((target / "inventory_cache_prod_sig").read_bytes(),b'fixture-signature')
            self.assertFalse((target / "login_token").exists())

    def test_unsigned_cache_is_not_copied(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "inventory_cache_prod").write_text('{"OfflineUserID":"OU_fixture"}')
            self.assertEqual(probe.copy_inventory_cache(root,root/'target',"OU_fixture")["status"],"unavailable")
            self.assertFalse((root/'target').exists())

    def test_wrong_side_and_malformed_events_fail(self):
        for text in [self.complete().replace('"client"', '"server"'), self.complete()+f"\n[DST_CLIENT:{self.token}] broken"]:
            self.assertFalse(probe.read_client_evidence(text, self.token)["passed"])

    def test_process_kill_is_waited(self):
        proc = Mock()
        proc.poll.side_effect = [None, 0]
        proc.wait.side_effect = [subprocess.TimeoutExpired("owned", 10), 0]
        probe.stop_owned_process(proc)
        proc.terminate.assert_called_once()
        proc.kill.assert_called_once()
        self.assertEqual(proc.wait.call_count, 2)

    def test_staging_is_unique_and_contains_explicit_script(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            script = root / "behavior.lua"
            script.write_text('return function(t) t.Done("ok") end')
            result = probe.stage_client_harness(root / "mods", self.token, "wanda", script)
            target = Path(result["staged"])
            self.assertEqual((target / "client_test.lua").read_text(), script.read_text())
            self.assertIn("PROBE_HAS_SCRIPT = true", (target / "probe_config.lua").read_text())
            with self.assertRaises(FileExistsError):
                probe.stage_client_harness(root / "mods", self.token)

    def test_missing_client_is_blocked_not_passed(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(probe.sys, "platform", "win32"):
            root = Path(temp)
            result = probe.run_client_probe(root, root / "storage", self.token, 11018, root / "evidence")
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["exit_code"], 2)
            self.assertFalse(result["passed"])

    def test_command_contains_isolated_storage_and_loopback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "bin64").mkdir()
            (root / "bin64/dontstarve_steam_x64.exe").touch()
            command = probe.client_command(root, root / "storage", 11018)
            self.assertEqual(command[command.index("-persistent_storage_root")+1], str(root / "storage"))
            self.assertEqual(command[-2:], ["+connect", "127.0.0.1:11018"])

    def test_orchestration_requires_named_assertion_and_cleans_owned_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / "game"
            (game / "mods").mkdir(parents=True)
            (game / "bin64").mkdir()
            (game / "bin64/dontstarve_dedicated_server_nullrenderer_x64.exe").touch()
            mod = root / "mod"
            mod.mkdir()
            (mod / "modinfo.lua").write_text('name="fixture"')
            done = threading.Event()
            runner = Mock()

            def stage(source, mods, token, index):
                target = mods / f"_dme_test_{token}_{index}"
                target.mkdir()
                return {"key": target.name, "staged": str(target)}

            def stage_runner(mods, token, *args):
                return stage(None, mods, token, "runner")

            def server(_runner, command, cwd, log, token, *args):
                log.write_text(f"[DME:{token}:READY]\n")
                done.wait(3)
                return {"passed": True}

            def client(*args, **kwargs):
                done.set()
                return {"status": "passed", "passed": True, "assertions": [{"name": "other", "ok": True}]}

            runner.stage_mod.side_effect = stage
            runner.stage_runner.side_effect = stage_runner
            runner.free_udp_port.return_value = 11018
            with patch.object(dst_workflow, "load_runner", return_value=runner), \
                 patch.object(dst_workflow, "port_is_free", return_value=True), \
                 patch.object(probe, "process_inventory", return_value=[]), \
                 patch.object(probe, "start_owned_steam", return_value={"owned": False}), \
                 patch.object(probe, "run_owned_server", side_effect=server), \
                 patch.object(probe, "run_client_probe", side_effect=client):
                result = probe.run_isolated_client_test({"dst_root": str(game)}, mod, root / "out", None,
                                                        expected=["required"], timeout=3)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["missing_assertions"], ["required"])
            self.assertTrue(result["cleanup"]["passed"])
            self.assertEqual(list((game / "mods").iterdir()), [])

    def test_cancel_stops_only_owned_server_process(self):
        class State:
            def __init__(self, *args):
                self.failure = None
            def consume(self, line):
                pass
            def passed(self):
                return False
        runner = Mock()
        runner.Outcome = State
        cancel = threading.Event()
        cancel.set()
        with tempfile.TemporaryDirectory() as temp:
            result = probe.run_owned_server(runner, [sys.executable, "-c", "import time; time.sleep(60)"],
                                            temp, Path(temp) / "server.log", self.token, 60, 1, [], cancel)
        self.assertFalse(result["passed"])
        self.assertTrue(result["process_exited"])
        self.assertLess(result["elapsed_seconds"], 10)

    @unittest.skipUnless(shutil.which("lua"), "需要已有 Lua 解释器执行自造 harness 回归")
    def test_async_done_waits_and_late_failure_is_not_lost(self):
        # 只提供游戏 API 的最小夹具；执行我们自己的 harness，不加载任何游戏文件。
        fixture = r'''
GLOBAL = _G
local callbacks, tasks, events = {}, {}, {}
local native_require = require
require = function(name) if name == "json" then return {encode=function(data) table.insert(events,data) return data.event end} end return native_require(name) end
modimport = function() PROBE_RUN_ID="async_test_123" PROBE_CHARACTER="wanda" PROBE_HAS_SCRIPT=true end
MODROOT = ""
setfenv = setfenv or function(fn) return fn end
TheNet = {IsDedicated=function() return false end}
TheWorld = {DoTaskInTime=function(_,_,fn) table.insert(tasks,fn) return {} end}
ThePlayer = {prefab="wanda",replica={health={classified={},Max=function() return 60 end}}}
GetModRPC = function() return {} end
GetClientModRPC = GetModRPC
SendModRPCToServer = function() end
SendModRPCToClient = function() end
AddModRPCHandler = function() end
AddClientModRPCHandler = function(_,name,fn) callbacks[name]=fn end
AddClassPostConstruct = function() end
AddPrefabPostInit = function() end
kleiloadlua = function() return function() return function(t)
    t.After(10, function() t.Assert("delayed", not FAIL_LATE) end)
    t.Done("requested before callback")
end end end
dofile(HARNESS_PATH)
callbacks.response("async_test_123","wanda",60)
local function count(kind) local n=0 for _,e in ipairs(events) do if e.event==kind then n=n+1 end end return n end
assert(count("done")==0,"Done bypassed pending After")
tasks[1]()
if FAIL_LATE then assert(count("done")==0,"failed callback still completed") else assert(count("done")==1,"successful pending callback did not complete") end
local bad=false for _,e in ipairs(events) do if e.event=="assert" and e.ok==false then bad=true end end
assert(bad==FAIL_LATE,"late assertion was lost")
'''
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test.lua"
            harness = (Path(__file__).parents[1] / "client_harness/modmain.lua").as_posix()
            for fail in (False, True):
                path.write_text(f'HARNESS_PATH={json.dumps(harness)}\nFAIL_LATE={str(fail).lower()}\n' + fixture, encoding="utf-8")
                result = subprocess.run([shutil.which("lua"), str(path)], capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
