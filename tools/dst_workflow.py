"""DST 需求验收入口：源码查证、静态检查、隔离测试、证据与部署。"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import uuid

from dst_static import check_resources

DEFAULT_CONFIG = Path.home() / ".ai/local/config/dst-mod-development/config.json"
PIN = "636bab848f552d3df843658526c460c6649e88b6"
ASSERT_RE = re.compile(r"\[DSTWF:([0-9a-f]+):ASSERT:(PASS|FAIL)\] ([A-Za-z0-9_.-]+)")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def regular_tree(path):
    path = Path(path)
    def inspect(item):
        stat = item.lstat()
        if item.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"拒绝链接或目录联接：{item}")
    inspect(path)
    def on_error(error):
        raise error
    for directory, dirs, files in os.walk(path, followlinks=False, onerror=on_error):
        for name in dirs + files:
            inspect(Path(directory) / name)


def mod_path(config, name):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError("模组名必须是工作区直属目录名")
    root = Path(config["workspace"]).resolve()
    path = root / name
    if path.resolve().parent != root or not (path / "modinfo.lua").is_file():
        raise ValueError(f"不是工作区直属模组：{path}")
    regular_tree(path)
    return path


def source_manifest(mod):
    from dst_deploy import runtime_manifest
    result = runtime_manifest(mod)
    test = mod / "dst_selftest.lua"
    if test.is_file():
        result["dst_selftest.lua"] = sha(test)
    return result


def validate_config(config):
    for key in ("workspace", "dst_root", "upstream_root", "evidence_root", "python"):
        if not config.get(key):
            raise ValueError(f"配置缺少 {key}")
    workspace, evidence = Path(config["workspace"]).resolve(), Path(config["evidence_root"]).resolve()
    if evidence == workspace or workspace in evidence.parents:
        raise ValueError("测试证据必须位于代码项目之外")
    expected = config.get("expected_upstream_commit", PIN)
    upstream = Path(config["upstream_root"])
    actual = subprocess.run(["git", "-C", str(upstream), "rev-parse", "HEAD"], capture_output=True,
                            text=True, timeout=15)
    if actual.returncode or actual.stdout.strip() != expected:
        raise ValueError(f"上游版本未验证：要求 {expected}，当前 {actual.stdout.strip() or '不可读'}")
    dirty = subprocess.run(["git", "-C", str(upstream), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, timeout=15)
    if dirty.returncode or dirty.stdout.strip():
        raise ValueError("上游源码有本地修改，不能沿用已验证版本")


def load_runner(config):
    path = Path(config["upstream_root"]) / "references/tools/engineering/scripts/dst_modtest.py"
    spec = importlib.util.spec_from_file_location("dst_upstream_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def doctor(config):
    validate_config(config)
    dst = Path(config["dst_root"])
    from importlib.metadata import version
    checks = {"python_3_10": sys.version_info >= (3, 10), "luaparser_4_1": version("luaparser") == "4.1.0",
              "scripts_zip": (dst / "data/databundles/scripts.zip").is_file(),
              "server": (dst / "bin64/dontstarve_dedicated_server_nullrenderer_x64.exe").is_file(),
              "client": (dst / "bin64/dontstarve_steam_x64.exe").is_file(), "mods": (dst / "mods").is_dir()}
    return {"status": "passed" if all(checks.values()) else "blocked", "checks": checks,
            "python": sys.executable, "upstream_commit": config.get("expected_upstream_commit", PIN)}


def static_check(config, mod, out, api_reviews=()):
    checker = Path(config["upstream_root"]) / "references/tools/engineering/scripts/check_api.py"
    report = out / "api.json"
    proc = subprocess.run([sys.executable, "-B", str(checker), str(mod), "--dst", config["dst_root"],
                           "--out", str(report)], capture_output=True, text=True, encoding="utf-8", timeout=180)
    (out / "api-console.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    if not report.is_file():
        return {"status": "blocked", "reason": "API 检查器未生成报告", "exit_code": proc.returncode}
    data = read_json(report)
    zip_hash = sha(Path(config["dst_root"]) / "data/databundles/scripts.zip")
    unresolved = []
    for call in data["calls"]:
        if call["status"] == "DECLARED":
            continue
        match = next((review for review in api_reviews if all(review.get(k) == call.get(k)
                     for k in ("file", "line", "side", "component", "method"))), None)
        valid = (match and match.get("reason") and match.get("evidence")
                 and match.get("mod_file_sha256") == sha(mod / call["file"])
                 and match.get("scripts_zip_sha256") == zip_hash)
        if not valid:
            unresolved.append(call)
    resources = check_resources(mod, Path(config["dst_root"]))
    status = "passed"
    if data["syntax_errors"] or resources["errors"] or proc.returncode not in (0, 2):
        status = "failed"
    elif unresolved or resources["reviews"]:
        status = "review_required"
    return {"status": status, "syntax_errors": data["syntax_errors"], "unresolved_calls": unresolved,
            "direct_calls": data["direct_calls"], "resources": resources, "report": str(report),
            "scripts_zip_sha256": zip_hash,
            "scope": "Lua 语法、直接组件声明、静态资源；不代表运行时或客户端通过"}


def load_plan(path, mod):
    plan = read_json(path)
    if plan.get("schema_version") != 1 or plan.get("mod") != mod.name or not plan.get("requirements"):
        raise ValueError("验收计划需要 schema_version=1、正确 mod 和非空 requirements")
    ids = set()
    for requirement in plan["requirements"]:
        ident = requirement.get("id", "")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", ident) or ident in ids or not requirement.get("description"):
            raise ValueError("验收项需要唯一 id 和需求描述")
        ids.add(ident)
        if requirement.get("stage") not in ("server", "client"):
            raise ValueError("验收项 stage 必须是 server/client；其他验收不能伪装已覆盖")
        assertions = requirement.get("assertions", [])
        if not assertions or any(not re.fullmatch(r"[A-Za-z0-9_.-]+", value) for value in assertions):
            raise ValueError("每项需求需要明确的断言 ID")
    return plan


def expected_assertions(plan, stage):
    return sorted({name for requirement in plan["requirements"] if requirement["stage"] == stage
                   for name in requirement["assertions"]})


def collect_assertions(text, run_id):
    result = {}
    for token, status, name in ASSERT_RE.findall(text):
        if token == run_id:
            result[name] = result.get(name, True) and status == "PASS"
    return result


def adapter_script(script, run_id, expected):
    body = Path(script).read_text(encoding="utf-8-sig")
    required = ",".join(json.dumps(x) for x in expected)
    return r'''TEST.TargetMod = "_dme_test___TOKEN___0"
local original_done = TEST.Done
local original_after = TEST.After
local observed = {}
local count = 0
local pending = 0
local requested_done = false
function TEST.Assert(name, ok, details)
    assert(type(name) == "string" and name:match("^[%w_.%-]+$"), "invalid assertion id")
    count = count + 1
    observed[name] = observed[name] ~= false and ok == true
    print("[DSTWF:__TOKEN__:ASSERT:" .. (ok == true and "PASS" or "FAIL") .. "] " .. name)
    if ok ~= true then TEST.Fail(name .. ": " .. tostring(details or "")) end
end
function TEST.Done(detail)
    requested_done = true
    if pending > 0 then return end
    if count == 0 then TEST.Fail("zero named assertions") return end
    for _, id in ipairs({__REQUIRED__}) do
        if observed[id] ~= true then TEST.Fail("missing/failed assertion: " .. id) return end
    end
    original_done(detail)
end
function TEST.After(seconds, callback)
    pending = pending + 1
    return original_after(seconds, function()
        local ok, err = xpcall(callback, tostring)
        pending = pending - 1
        if not ok then TEST.Fail(err) end
        if requested_done and pending == 0 then TEST.Done("all scheduled assertions completed") end
    end)
end
local legacy = {
    target_mod = TEST.TargetMod,
    after = TEST.After,
    assert = TEST.Assert,
    emit = function(value) print("[DSTWF detail]", tostring(value)) end,
    spawn = function(prefab)
        local ok, inst = pcall(SpawnPrefab, prefab)
        TEST.Assert("custom_spawn_" .. prefab, ok and inst ~= nil, tostring(inst))
        return ok and inst or nil
    end,
    remove = function(inst) if inst and inst:IsValid() then inst:Remove() end end,
}
TEST.Legacy = legacy
local function scenario()
__BODY__
end
local returned = scenario()
if type(returned) == "function" then
    TEST.Fail("returned function is not completion; use an explicit scenario and TEST.Done")
end
'''.replace("__TOKEN__", run_id).replace("__REQUIRED__", required).replace("__BODY__", body)


def remove_owned(path, parent, expected_name):
    path, parent = Path(path), Path(parent).resolve()
    if path.name != expected_name or path.resolve().parent != parent or path.resolve() == parent:
        raise ValueError(f"拒绝清理非本轮路径：{path}")
    if path.exists():
        regular_tree(path)
        shutil.rmtree(path)


def port_is_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False


def server_test(config, mod, out, script, expected=(), timeout=240):
    runner = load_runner(config)
    token = uuid.uuid4().hex
    dst = Path(config["dst_root"])
    storage = out / "runtime" / token
    adapter = out / "server-scenario.lua"
    adapter.write_text(adapter_script(script, token, expected), encoding="utf-8")
    record = {"run_id": token, "status": "running", "source_sha256": source_manifest(mod),
              "script_sha256": sha(script), "staged": [], "scope": "隔离专服，具名业务断言"}
    port = None
    try:
        staged = runner.stage_mod(mod, dst / "mods", token, 0)
        record["staged"].append(staged)
        harness = runner.stage_runner(dst / "mods", token, adapter, 2, [staged["key"]])
        record["staged"].append(harness)
        port = runner.free_udp_port()
        runner.write_cluster(storage, [staged["key"], harness["key"]], port)
        exe = dst / "bin64/dontstarve_dedicated_server_nullrenderer_x64.exe"
        command = [str(exe), "-offline", "-console", "-persistent_storage_root", str(storage),
                   "-conf_dir", "DME", "-cluster", "Cluster", "-shard", "Master", "-port", str(port)]
        record.update(command=command, port=port)
        write_json(out / "server.json", record)
        result = runner.run_server(command, exe.parent, out / "server.log", token,
                                   timeout, 3, True, [staged["key"]])
        assertions = collect_assertions((out / "server.log").read_text(encoding="utf-8"), token)
        covered = bool(assertions) and all(assertions.values()) and all(assertions.get(x) for x in expected)
        record.update(status="passed" if result["passed"] and covered else "failed",
                      result=result, assertions=assertions,
                      missing_assertions=[x for x in expected if not assertions.get(x)])
    finally:
        cleanup_errors = []
        # Derive ownership from our UUID even if upstream staging failed before returning its manifest.
        for key in (f"_dme_test_{token}_0", f"_dme_test_{token}_runner"):
            try:
                remove_owned(dst / "mods" / key, dst / "mods", key)
            except (OSError, ValueError) as exc:
                cleanup_errors.append(str(exc))
        try:
            remove_owned(storage, out / "runtime", token)
        except (OSError, ValueError) as exc:
            cleanup_errors.append(str(exc))
        if port is not None and not port_is_free(port):
            cleanup_errors.append(f"本轮 UDP 端口 {port} 未释放")
        record["cleanup"] = {"passed": not cleanup_errors, "errors": cleanup_errors}
        if cleanup_errors:
            record["status"] = "failed"
        write_json(out / "server.json", record)
    return record


def resolve_script(config, value):
    workspace = Path(config["workspace"]).resolve()
    path = (workspace / value).resolve()
    if workspace not in path.parents or not path.is_file():
        raise ValueError(f"测试脚本必须是当前工作区内文件：{value}")
    return path


def verify(config, mod, out, plan_path, timeout):
    plan = load_plan(plan_path, mod)
    result = {"status": "running", "plan": str(Path(plan_path).resolve()), "plan_sha256": sha(plan_path),
              "scope": plan.get("scope", "仅覆盖列出的验收项"), "uncovered": plan.get("uncovered", []),
              "requirements": plan["requirements"], "stages": {}, "scenario_sha256": {}}
    result["stages"]["check"] = static_check(config, mod, out, plan.get("api_reviews", []))
    if result["stages"]["check"]["status"] != "passed":
        result["status"] = result["stages"]["check"]["status"]
        return result
    expected = expected_assertions(plan, "server")
    if expected:
        script = resolve_script(config, plan.get("server_script", mod.name + "/dst_selftest.lua"))
        result["scenario_sha256"][str(script)] = sha(script)
        result["stages"]["server"] = server_test(config, mod, out, script, expected, timeout)
    if expected_assertions(plan, "client"):
        from dst_client_probe import run_isolated_client_test
        script = resolve_script(config, plan["client_script"])
        server_setup = resolve_script(config, plan["client_server_script"]) if plan.get("client_server_script") else None
        result["scenario_sha256"][str(script)] = sha(script)
        if server_setup:
            result["scenario_sha256"][str(server_setup)] = sha(server_setup)
        result["stages"]["client"] = run_isolated_client_test(config, mod, out / "client", script,
                expected_assertions(plan, "client"), timeout, server_script=server_setup)
    statuses = [stage["status"] for stage in result["stages"].values()]
    result["status"] = "passed" if all(x == "passed" for x in statuses) else ("failed" if "failed" in statuses else "blocked")
    if result["plan_sha256"] != sha(plan_path) or any(sha(p) != h for p, h in result["scenario_sha256"].items()):
        result.update(status="failed", reason="验收期间计划或场景脚本改变，必须重新运行")
    return result


def require_verified(config, mod, evidence):
    """部署只消费明确指定、本轮输入仍匹配的完整验收报告。"""
    if not evidence:
        raise ValueError("部署 --apply 需要 --verified <verify生成的result.json>，先完成需求验收")
    path = Path(evidence).resolve()
    root = Path(config["evidence_root"]).resolve()
    if root not in path.parents or path.name != "result.json":
        raise ValueError("验收报告必须来自配置的证据目录")
    report = read_json(path)
    if report.get("command") != "verify" or report.get("status") != "passed" or report.get("mod") != str(mod):
        raise ValueError("需要此模组的成功 verify 报告，单项测试结果不足以部署")
    if report.get("source_sha256") != source_manifest(mod):
        raise ValueError("源码已变化，旧验收报告失效")
    if report.get("scripts_zip_sha256") != sha(Path(config["dst_root"]) / "data/databundles/scripts.zip"):
        raise ValueError("游戏版本已变化，需要重新验收")
    if report.get("upstream_commit") != config.get("expected_upstream_commit", PIN):
        raise ValueError("测试工具版本已变化，需要重新验收")
    plan = Path(report.get("plan", ""))
    if not plan.is_file() or report.get("plan_sha256") != sha(plan):
        raise ValueError("验收标准已变化或不可读，需要重新验收")
    if not report.get("scenario_sha256") or any(not Path(p).is_file() or sha(p) != h for p,h in report["scenario_sha256"].items()):
        raise ValueError("验收脚本已变化，需要重新验收")
    if report.get("tool_sha256") != tool_manifest():
        raise ValueError("本地测试工具已变化，需要重新验收")
    return report


def tool_manifest():
    root = Path(__file__).parent
    paths = list(root.glob("dst*.py")) + list((root / "client_harness").glob("*.lua"))
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(paths)}


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "check", "test", "verify", "deploy"):
        p = sub.add_parser(name)
        p.add_argument("--config", default=str(DEFAULT_CONFIG))
        if name != "doctor":
            p.add_argument("--mod", default="wanda-skilltree")
        if name in ("test", "verify"):
            p.add_argument("--timeout", type=int, default=240)
        if name == "test":
            p.add_argument("--script")
        if name in ("check", "verify"):
            p.add_argument("--plan")
        if name == "deploy":
            p.add_argument("--apply", action="store_true")
            p.add_argument("--verified")
    args = parser.parse_args()
    out, result = None, None
    try:
        config = read_json(args.config)
        validate_config(config)
        if args.command == "doctor":
            result = doctor(config)
        else:
            mod = mod_path(config, args.mod)
            out = Path(config["evidence_root"]) / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8])
            out.mkdir(parents=True, exist_ok=False)
            before = source_manifest(mod)
            tools_before = tool_manifest()
            game_before = sha(Path(config["dst_root"]) / "data/databundles/scripts.zip")
            if args.command == "check":
                plan = load_plan(args.plan, mod) if args.plan else {}
                result = static_check(config, mod, out, plan.get("api_reviews", []))
            elif args.command == "test":
                default_plan = Path(config["workspace"]) / "tools/acceptance" / (mod.name + ".json")
                default_script = read_json(default_plan).get("server_script") if default_plan.is_file() else None
                script = resolve_script(config, args.script or default_script or mod.name + "/dst_selftest.lua")
                result = server_test(config, mod, out, script, timeout=args.timeout)
            elif args.command == "verify":
                plan = args.plan or str(Path(config["workspace"]) / "tools/acceptance" / (mod.name + ".json"))
                result = verify(config, mod, out, plan, args.timeout)
            else:
                from dst_deploy import deploy_mod
                if args.apply:
                    require_verified(config, mod, args.verified)
                result = deploy_mod(config["workspace"], config["dst_root"], args.mod,
                                    config["evidence_root"], apply=args.apply)
            if before != source_manifest(mod):
                result.update(status="failed", reason="执行期间源码改变，结果不能归属当前源码")
            if tools_before != tool_manifest() or game_before != sha(Path(config["dst_root"]) / "data/databundles/scripts.zip"):
                result.update(status="failed", reason="执行期间测试工具或游戏版本改变，需重新运行")
            result.update(command=args.command, mod=str(mod), source_sha256=before,
                          scripts_zip_sha256=game_before, tool_sha256=tools_before,
                          upstream_commit=config.get("expected_upstream_commit", PIN),
                          generated_at=datetime.now(timezone.utc).isoformat(), evidence_dir=str(out))
    except Exception as exc:
        result = {"status": "blocked", "reason": str(exc), "command": args.command}
    finally:
        if out is not None and result is not None:
            write_json(out / "result.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in ("passed", "preview", "applied", "unchanged") else (1 if result["status"] == "failed" else 2)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(cli())
