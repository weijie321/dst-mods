"""在隔离存档中验证真实 DST 客户端；没有客户端证据时绝不报告通过。"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid


HARNESS = Path(__file__).with_name("client_harness")
REQUIRED_EVENTS = {"ready", "player", "hud", "replica", "done"}
FATAL_PATTERNS = ("lua error", "error loading mod!", "error loading modinfo.lua", "[critical]", "assertion failed")


def validate_run_id(run_id: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_]{8,80}", run_id):
        raise ValueError("run_id 必须为 8–80 位字母、数字或下划线")


def stage_client_harness(mods_root, run_id, character="wanda", script=None):
    """由服务端编排器启用返回的 key；复制目录归编排器按 manifest 清理。"""
    validate_run_id(run_id)
    if not re.fullmatch(r"[a-z][a-z0-9_]*", character):
        raise ValueError("角色 Prefab 名无效")
    if script is not None and not Path(script).is_file():
        raise ValueError(f"客户端断言脚本不存在：{script}")
    key = f"_dstwf_client_{run_id}"
    target = Path(mods_root).resolve() / key
    shutil.copytree(HARNESS, target)
    config = (f'PROBE_RUN_ID = "{run_id}"\nPROBE_CHARACTER = "{character}"\n'
              f'PROBE_HAS_SCRIPT = {"true" if script else "false"}\n')
    (target / "probe_config.lua").write_text(config, encoding="utf-8")
    if script:
        shutil.copyfile(script, target / "client_test.lua")
    hashes = {p.relative_to(target).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(target.rglob("*")) if p.is_file()}
    return {"key": key, "staged": str(target), "sha256": hashes,
            "character": character, "behavior_script": str(Path(script).resolve()) if script else None}


def client_command(dst_root, storage, server_port):
    dst = Path(dst_root).resolve()
    exe = next((p for p in (dst / "bin64/dontstarve_steam_x64.exe", dst / "bin/dontstarve_steam.exe")
                if p.is_file()), None)
    if exe is None:
        raise ValueError("未找到真实 DST 客户端程序")
    if not 1 <= server_port <= 65535:
        raise ValueError("服务端端口无效")
    # +connect 与存储参数均存在于本机客户端；无键盘注入和全局配置改动。
    return [str(exe), "-offline", "-console", "-persistent_storage_root", str(storage),
            "-conf_dir", "DSTClientProbe", "+connect", f"127.0.0.1:{server_port}"]


def copy_matching_inventory_cache(conf, run_id):
    """仅原样复用当前 Steam 账号的签名离线物品缓存；不读取登录凭据。"""
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess") as key:
            account = int(winreg.QueryValueEx(key, "ActiveUser")[0])
    except OSError:
        return {"status": "unavailable", "reason": "当前活动 Steam 账号不可读"}
    if not account:
        return {"status": "unavailable", "reason": "Steam 尚未提供活动账号"}
    offline_id = "OU_" + str(account + 76561197960265728)
    source = Path.home() / "Documents/Klei/DoNotStarveTogether" / str(account) / "client_save"
    account_root = Path(conf) / str(account)
    result = copy_inventory_cache(source, account_root / "client_save", offline_id)
    if result["status"] == "copied_for_engine_validation":
        # 原版 Start 通过 client_save/../customcommands.lua 读取本账号启动命令。
        startup = '''print("[DST_CLIENT_DIAG:__TOKEN__] customcommands_loaded")
if TheInventory:HasSupportForOfflineSkins() and not TheInventory:HasDownloadedInventory() then
    TheInventory:ForceLoadOfflineCache()
end
print("[DST_CLIENT_DIAG:__TOKEN__] inventory_loaded=" .. tostring(TheInventory:HasDownloadedInventory()))
'''.replace("__TOKEN__", run_id)
        (account_root / "customcommands.lua").write_text(startup, encoding="utf-8")
    return result


def copy_inventory_cache(source, target, offline_id):
    source, target = Path(source), Path(target)
    cache, signature = source / "inventory_cache_prod", source / "inventory_cache_prod_sig"
    if not cache.is_file() or not signature.is_file():
        return {"status": "unavailable", "reason": "当前账号没有完整签名离线物品缓存"}
    data = json.loads(cache.read_text(encoding="utf-8"))
    if data.get("OfflineUserID") != offline_id:
        return {"status": "unavailable", "reason": "物品缓存不属于当前活动账号"}
    target.mkdir(parents=True)
    hashes = {}
    for path in (cache, signature):
        shutil.copyfile(path, target / path.name)
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"status": "copied_for_engine_validation", "same_account": True, "sha256": hashes}


def read_client_evidence(text, run_id):
    """只接受本轮、真实客户端端别的结构化事件；普通服务端 DONE 无效。"""
    validate_run_id(run_id)
    marker = f"[DST_CLIENT:{run_id}] "
    events, failures, blockers = [], [], []
    for line in text.splitlines():
        if marker in line:
            try:
                event = json.loads(line.split(marker, 1)[1])
            except (ValueError, TypeError):
                failures.append("本轮客户端事件不是有效 JSON")
                continue
            if not isinstance(event, dict) or event.get("side") != "client":
                failures.append("本轮事件缺少真实客户端端别")
                continue
            events.append(event)
            if event.get("event") == "blocked":
                blockers.append(str(event.get("details") or "客户端环境不可用"))
            if event.get("event") == "fail" or (event.get("event") == "assert" and event.get("ok") is not True):
                failures.append(str(event.get("name") or event.get("details") or "客户端断言失败"))
        if any(pattern in line.lower() for pattern in FATAL_PATTERNS):
            failures.append(line.strip())
    seen = {event.get("event") for event in events}
    assertions = [e for e in events if e.get("event") == "assert"]
    return {"passed": REQUIRED_EVENTS <= seen and not failures and not blockers and bool(assertions),
            "events": events, "assertions": assertions, "failures": failures,
            "blockers": blockers,
            "missing_events": sorted(REQUIRED_EVENTS - seen)}


def stop_owned_process(proc):
    """仅停止此工具创建的句柄，kill 后同样等待退出。"""
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
    return proc.poll()


def run_client_probe(dst_root, storage_root, run_id, server_port, evidence_dir,
                     timeout=120, grace=3):
    validate_run_id(run_id)
    if not all(math.isfinite(v) for v in (timeout, grace)) or timeout <= 0 or grace < 0:
        raise ValueError("客户端 timeout/grace 无效")
    evidence = Path(evidence_dir).resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    storage = Path(storage_root).resolve() / f"client_{run_id}"
    result = {"status": "blocked", "passed": False, "run_id": run_id,
              "scope": "真实客户端连接、HUD、Replica 以及显式客户端断言；不代表像素视觉验收",
              "storage": str(storage), "events": [], "assertions": []}
    proc = None
    try:
        if sys.platform != "win32":
            raise ValueError("当前客户端执行器仅支持 Windows")
        command = client_command(dst_root, storage, server_port)
        # 拒绝复用旧证据；只在本次独立目录创建设置与日志。
        storage.mkdir(parents=True, exist_ok=False)
        conf = storage / "DSTClientProbe"
        conf.mkdir()
        (conf / "client.ini").write_text("[MISC]\nconsole_enabled = true\nwarn_mods_enabled = false\n[GRAPHICS]\nfullscreen = false\n", encoding="utf-8")
        result["offline_inventory_cache"] = copy_matching_inventory_cache(conf, run_id)
        result.update(command=command, client_log=str(conf / "client_log.txt"))
        console_path = evidence / "client-console.log"
        with console_path.open("w", encoding="utf-8") as console:
            proc = subprocess.Popen(command, cwd=Path(command[0]).parent,
                                    stdin=subprocess.DEVNULL, stdout=console, stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NO_WINDOW,
                                    env={**os.environ, "SteamAppId": "322330", "SteamGameId": "322330"})
            result["pid"] = proc.pid
            start = time.monotonic()
            done_at = None
            while time.monotonic() - start < timeout:
                console.flush()
                logs = [console_path, conf / "client_log.txt"]
                text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in logs if p.is_file())
                parsed = read_client_evidence(text, run_id)
                result.update(parsed)
                if parsed["blockers"]:
                    result.update(status="blocked", reason="；".join(parsed["blockers"]))
                    break
                if parsed["failures"]:
                    result.update(status="failed", reason="客户端日志或断言失败")
                    break
                if parsed["passed"]:
                    done_at = done_at or time.monotonic()
                    if time.monotonic() - done_at >= grace:
                        result.update(status="passed")
                        break
                if proc.poll() is not None:
                    result.update(passed=False, reason="客户端在验证完成前退出；检查 Steam/图形环境和连接日志")
                    break
                time.sleep(0.25)
            else:
                result.update(passed=False, reason="客户端连接或断言未在期限内完成", timeout=True)
            result["elapsed_seconds"] = round(time.monotonic() - start, 2)
        result["console_log"] = str(console_path)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result.update(status="blocked", passed=False, reason=str(exc))
    finally:
        if proc is not None:
            result["returncode"] = stop_owned_process(proc)
            result["process_exited"] = proc.poll() is not None
            final_text = "\n".join(p.read_text(encoding="utf-8", errors="replace")
                                   for p in (console_path, conf / "client_log.txt") if p.is_file())
            final_evidence = read_client_evidence(final_text, run_id)
            result.update(events=final_evidence["events"], assertions=final_evidence["assertions"],
                          failures=final_evidence["failures"], blockers=final_evidence["blockers"],
                          missing_events=final_evidence["missing_events"])
            if final_evidence["failures"]:
                result.update(status="failed", passed=False, reason="客户端最终日志或断言失败")
            elif final_evidence["blockers"]:
                result.update(status="blocked", passed=False, reason="；".join(final_evidence["blockers"]))
            source_log = conf / "client_log.txt"
            if source_log.is_file():
                saved_log = evidence / "client.log"
                shutil.copyfile(source_log, saved_log)
                result["client_log"] = str(saved_log)
        result["exit_code"] = 0 if result["status"] == "passed" else (1 if result["status"] == "failed" else 2)
        (evidence / "client-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def process_inventory():
    """只记录游戏/Steam PID 和父 PID，不读取命令行或账号数据。"""
    if sys.platform != "win32":
        return []
    command = ("@(Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'dontstarve*' "
               "-or $_.Name -in @('steam.exe','steamwebhelper.exe','gameoverlayui.exe') } "
               "| Select-Object ProcessId,ParentProcessId,Name) | ConvertTo-Json -Compress")
    proc = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True,
                          text=True, encoding="utf-8", timeout=15,
                          creationflags=subprocess.CREATE_NO_WINDOW)
    if proc.returncode:
        raise OSError("无法读取游戏进程归属")
    data = json.loads(proc.stdout.strip() or "[]")
    return data if isinstance(data, list) else [data]


def run_owned_server(runner, command, cwd, log_path, run_id, timeout, grace, expected, cancel):
    """本地拥有进程句柄，复用上游判定；客户端阻塞可立即取消，不改上游源码。"""
    state = runner.Outcome(run_id, expected)
    start, done_at = time.monotonic(), None
    proc = None
    log_path = Path(log_path)
    try:
        with log_path.open("w", encoding="utf-8") as output:
            proc = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL,
                                    stdout=output, stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            while True:
                text = log_path.read_text(encoding="utf-8", errors="replace")
                for line in text.splitlines():
                    state.consume(line)
                now = time.monotonic()
                if state.failure:
                    break
                if state.passed():
                    done_at = done_at or now
                    if now - done_at >= grace:
                        break
                if cancel.is_set():
                    state.failure = "客户端未完成，取消本轮隔离专服"
                    break
                if now - start >= timeout:
                    state.failure = "本轮客户端/专服验证超时"
                    break
                if proc.poll() is not None:
                    state.failure = "专服在观察窗完成前退出"
                    break
                cancel.wait(0.1)
    finally:
        if proc is not None:
            stop_owned_process(proc)
            for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
                state.consume(line)
    return {**vars(state), "passed": state.passed(), "pid": proc.pid if proc else None,
            "process_exited": proc is None or proc.poll() is not None,
            "returncode": proc.returncode if proc else None,
            "elapsed_seconds": round(time.monotonic() - start, 2), "log": str(log_path)}


def start_owned_steam(dst, before):
    if any(p["Name"].lower() == "steam.exe" for p in before):
        return {"owned": False, "status": "already_running"}
    exe = Path(dst).parents[2] / "steam.exe"
    if not exe.is_file():
        raise ValueError("Steam 未运行且无法定位已有 Steam.exe；不安装、不自动登录")
    proc = subprocess.Popen([str(exe), "-silent"], cwd=exe.parent, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    record = {"owned": True, "pid": proc.pid, "exe": str(exe), "status": "started", "command": [str(exe), "-silent"]}
    for _ in range(60):
        processes = process_inventory()
        if any(p["Name"].lower() == "steamwebhelper.exe" for p in processes):
            record["processes"] = processes
            record["session"] = steam_session_state()
            return record
        time.sleep(0.5)
    record["status"] = "started_not_ready"
    return record


def steam_session_state():
    """仅返回是否存在活动账号，绝不输出账号 ID 或读取登录凭据。"""
    if sys.platform != "win32":
        return {"active_user": None}
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess") as key:
            value = winreg.QueryValueEx(key, "ActiveUser")[0]
        return {"active_user": bool(value)}
    except OSError:
        return {"active_user": None}


def stop_owned_steam(record):
    if not record.get("owned"):
        return []
    processes = process_inventory()
    if any(p["Name"].lower().startswith("dontstarve") and "dedicated_server" not in p["Name"].lower() for p in processes):
        return ["仍有游戏进程，保留 Steam 避免影响玩家"]
    subprocess.run([record["exe"], "-shutdown"], cwd=Path(record["exe"]).parent,
                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(40):
        remaining = [p for p in process_inventory() if p["Name"].lower() in ("steam.exe", "steamwebhelper.exe", "gameoverlayui.exe")]
        if not remaining:
            record["processes_exited"] = True
            return []
        time.sleep(0.5)
    record["remaining"] = remaining
    return ["本轮启动的 Steam 在官方 -shutdown 后仍未完全退出"]


def run_isolated_client_test(config, mod_path, evidence_dir, script, expected=(), timeout=180,
                             server_script=None):
    """复用上游快照/专服 runner，串联真实客户端证据与独立存档清理。"""
    from dst_workflow import load_runner, remove_owned, port_is_free, source_manifest, write_json

    runner = load_runner(config)
    token = uuid.uuid4().hex
    out = Path(evidence_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    mod = Path(mod_path).resolve()
    dst = Path(config["dst_root"]).resolve()
    runtime_parent = out / "runtime"
    storage = runtime_parent / token
    record = {"run_id": token, "status": "blocked", "source_sha256": source_manifest(mod),
              "staged": [], "expected_assertions": list(expected), "assertions": {},
              "scope": "独立专服 + 真实远端客户端；只覆盖实际具名断言，不证明像素画面"}
    port, thread = None, None
    server_result = {}
    before_processes = []
    cancel = threading.Event()
    try:
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("客户端测试总时限必须为正数")
        before_processes = process_inventory()
        record["processes_before"] = before_processes
        record["steam"] = start_owned_steam(dst, before_processes)
        staged = runner.stage_mod(mod, dst / "mods", token, 0)
        record["staged"].append(staged)
        client_harness = stage_client_harness(dst / "mods", token, config.get("client_character", "wanda"), script)
        record["staged"].append(client_harness)
        if script:
            shutil.copyfile(script, out / "client-scenario.lua")
            record["script_sha256"] = hashlib.sha256(Path(script).read_bytes()).hexdigest()
        setup = ""
        if server_script:
            setup = Path(server_script).read_text(encoding="utf-8-sig")
            shutil.copyfile(server_script, out / "client-server-setup.lua")
            record["server_script_sha256"] = hashlib.sha256(Path(server_script).read_bytes()).hexdigest()
        bridge = out / "client-server-scenario.lua"
        bridge.write_text('''local token = "__TOKEN__"
TheWorld:ListenForEvent("dstwf_client_done", function(_, data)
    if data == nil or data.run_id ~= token then return end
    if data.ok then TEST.Done("真实客户端已完成") else TEST.Fail(data.details or "客户端断言失败") end
end)
local function prepare()
__SETUP__
end
local result = prepare()
if type(result) == "function" then result(TEST) end
'''.replace("__TOKEN__", token).replace("__SETUP__", setup), encoding="utf-8")
        keys = [staged["key"], client_harness["key"]]
        server_harness = runner.stage_runner(dst / "mods", token, bridge, 2, keys)
        record["staged"].append(server_harness)
        port = runner.free_udp_port()
        runner.write_cluster(storage, keys + [server_harness["key"]], port)
        exe = next((p for p in (dst / "bin64/dontstarve_dedicated_server_nullrenderer_x64.exe",
                              dst / "bin/dontstarve_dedicated_server_nullrenderer.exe") if p.is_file()), None)
        if exe is None:
            raise ValueError("专服程序不存在")
        command = [str(exe), "-offline", "-console", "-persistent_storage_root", str(storage),
                   "-conf_dir", "DME", "-cluster", "Cluster", "-shard", "Master", "-port", str(port)]
        record.update(server_command=command, port=port, storage=str(storage))
        write_json(out / "client-stage.json", record)
        server_log = out / "client-server.log"

        def run_server():
            try:
                server_result.update(run_owned_server(runner, command, exe.parent, server_log, token,
                                                      timeout, 5, keys, cancel))
            except Exception as exc:
                server_result.update(passed=False, failure=str(exc))

        thread = threading.Thread(target=run_server, name=f"dst-client-server-{token}")
        thread.start()
        started = time.monotonic()
        ready = f"[DME:{token}:READY]"
        while thread.is_alive() and time.monotonic() - started < timeout:
            text = server_log.read_text(encoding="utf-8", errors="replace") if server_log.is_file() else ""
            if ready in text:
                remaining = max(1, timeout - (time.monotonic() - started) - 5)
                client = run_client_probe(dst, storage, token, port, out, timeout=remaining)
                record["client"] = client
                assertions = {}
                for assertion in client.get("assertions", []):
                    name = assertion.get("name")
                    if name:
                        assertions[name] = assertions.get(name, True) and assertion.get("ok") is True
                record["assertions"] = assertions
                record["missing_assertions"] = [name for name in expected if not assertions.get(name)]
                record["status"] = client["status"]
                if client.get("reason"):
                    record["reason"] = client["reason"]
                if record["missing_assertions"] and client["status"] == "passed":
                    record.update(status="failed", reason="客户端缺少要求的通过断言")
                break
            time.sleep(0.25)
        else:
            record.update(reason="隔离专服未达到本轮 READY", status="blocked")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        record.update(status="blocked", reason=str(exc))
    finally:
        # 客户端环境阻塞时及时取消自有专服；先确认退出，再清理运行目录。
        if thread is not None:
            if record["status"] != "passed":
                cancel.set()
            thread.join(timeout=timeout + 30)
            record["server"] = server_result
            if record["status"] == "passed" and not server_result.get("passed"):
                record.update(status="failed", reason="专服未确认本轮客户端完成")
        cleanup_errors = []
        if thread is not None and thread.is_alive():
            cleanup_errors.append("自有专服线程未退出，保留运行目录")
            record.update(status="failed", cleanup={"passed": False, "errors": cleanup_errors})
            write_json(out / "client-stage.json", record)
            return record
        for key in (f"_dme_test_{token}_0", f"_dme_test_{token}_runner", f"_dstwf_client_{token}"):
            try:
                remove_owned(dst / "mods" / key, dst / "mods", key)
            except (OSError, ValueError) as exc:
                cleanup_errors.append(str(exc))
        try:
            remove_owned(storage, runtime_parent, token)
        except (OSError, ValueError) as exc:
            cleanup_errors.append(str(exc))
        if port is not None and not port_is_free(port):
            cleanup_errors.append(f"本轮 UDP 端口 {port} 未释放")
        try:
            cleanup_errors.extend(stop_owned_steam(record.get("steam", {})))
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            cleanup_errors.append(str(exc))
        try:
            after = process_inventory()
            record["processes_after"] = after
            old_ids = {p["ProcessId"] for p in before_processes}
            created = [p for p in after if p["ProcessId"] not in old_ids]
            if created:
                owned = {record.get("client", {}).get("pid"), server_result.get("pid"), record.get("steam", {}).get("pid")}
                for _ in created:
                    owned.update(p["ProcessId"] for p in created if p["ParentProcessId"] in owned)
                remaining_owned = [p for p in created if p["ProcessId"] in owned]
                record["new_remaining_processes"] = remaining_owned
                record["unrelated_new_processes"] = [p for p in created if p["ProcessId"] not in owned]
                if remaining_owned:
                    cleanup_errors.append("检测到本轮拥有的游戏/Steam进程残留")
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            cleanup_errors.append(str(exc))
        record["cleanup"] = {"passed": not cleanup_errors, "errors": cleanup_errors}
        if cleanup_errors:
            record["status"] = "failed"
        record["exit_code"] = 0 if record["status"] == "passed" else (1 if record["status"] == "failed" else 2)
        write_json(out / "client-stage.json", record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dst", required=True)
    parser.add_argument("--storage-root", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--server-port", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    result = run_client_probe(args.dst, args.storage_root, args.run_id, args.server_port, args.out, args.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
