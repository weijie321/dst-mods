from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


APP_NAME = "CrashTrace Viewer"
DEFAULT_OUTPUT_FILE_NAME = "latest_crashtrace_report.txt"
DEFAULT_ROOT = Path.home() / "Documents" / "Klei" / "DoNotStarveTogether"
DEDICATED_SERVER_DIRS = ["MyDediServer"]
BEGIN = "[CrashTrace][ERROR] report_begin"
END = "[CrashTrace][ERROR] report_end"
TRACEBACK_BEGIN = "[CrashTrace][ERROR] traceback_begin"
TRACEBACK_END = "[CrashTrace][ERROR] traceback_end"
TRACE_PREFIX = "[CrashTrace][TRACE] "
ERROR_PREFIX = "[CrashTrace][ERROR] "
TRACE_FILE_RE = re.compile(r"(\.\./mods/[^\s]+\.lua)\((\d+),\d+\) in function '([^']+)'")
TRACE_FILE_RE_ALT = re.compile(r"(\.\./mods/[^\s]+\.lua)\((\d+),\d+\)")
MOD_SOURCE_RE = re.compile(r"\.\./mods/([^/]+)/")

HOOK_LABELS = {
    "AddPlayerPostInit": "玩家初始化回调",
    "AddPrefabPostInit": "实体初始化回调",
    "AddPrefabPostInitAny": "任意实体初始化回调",
    "AddComponentPostInit": "组件初始化回调",
    "AddGamePostInit": "游戏初始化回调",
    "AddSimPostInit": "模拟初始化回调",
    "ListenForEvent": "事件监听",
    "DoTaskInTime": "延时任务",
    "DoPeriodicTask": "周期任务",
    "native_lua_error": "原生 Lua 异常",
}

ACTION_LABELS = {
    "player_post_init": "玩家初始化",
    "prefab_post_init": "实体初始化",
    "prefab_post_init_any": "任意实体初始化",
    "component_post_init": "组件初始化",
    "game_post_init": "游戏初始化",
    "sim_post_init": "模拟初始化",
    "event_listener": "事件监听触发",
    "task_in_time": "延时任务触发",
    "periodic_task": "周期任务触发",
    "native_lua_error": "原生 Lua 异常",
    "pick_action": "采集动作",
    "attack_action": "攻击动作",
    "equip_action": "装备动作",
    "build_action": "建造动作",
}

PREFAB_LABELS = {
    "grass": "草",
    "wilson": "威尔逊",
    "player": "玩家",
    "game": "游戏",
    "sim": "模拟器",
    "sapling": "树枝苗",
    "reeds": "芦苇",
    "berrybush": "浆果丛",
    "berrybush2": "浆果丛",
    "berrybush_juicy": "多汁浆果丛",
    "cutgrass": "草",
    "twigs": "树枝",
    "pickable": "可采集物",
    "willow": "薇洛",
    "wolfgang": "沃尔夫冈",
    "wendy": "温蒂",
    "wx78": "WX-78",
    "wickerbottom": "薇克巴顿",
    "woodie": "伍迪",
    "wes": "韦斯",
    "waxwell": "麦斯威尔",
    "wathgrithr": "薇格弗德",
    "webber": "韦伯",
    "winona": "薇诺娜",
    "wortox": "沃拓克斯",
    "wormwood": "沃姆伍德",
    "wurt": "沃特",
    "walter": "沃尔特",
    "wanda": "旺达",
    "carrot_planted": "胡萝卜",
    "flower": "花",
    "flint": "燧石",
    "rock1": "岩石",
    "evergreen": "常青树",
    "deciduoustree": "桦栗树",
    "marsh_bush": "尖刺灌木",
    "cactus": "仙人掌",
}

EVENT_LABELS = {
    "picked": "采集",
    "death": "死亡",
    "attacked": "被攻击",
    "onremove": "移除",
    "equip": "装备",
    "unequip": "卸下",
    "builditem": "制作",
    "onbuilt": "建造完成",
    "harvest": "收获",
    "working": "作业",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", help="Override DST log root directory.")
    parser.add_argument("--output", help="Write report text to this file.")
    parser.add_argument("--open-output", action="store_true", help="Open the generated report file.")
    return parser.parse_args()


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


def resolve_output_path(output: str | None) -> Path:
    if output:
        return Path(output).expanduser().resolve()

    return get_app_dir() / DEFAULT_OUTPUT_FILE_NAME


def resolve_root_path(root: str | None) -> Path:
    if root:
        return Path(root).expanduser().resolve()

    return DEFAULT_ROOT


def should_open_output(args: argparse.Namespace) -> bool:
    return args.open_output or bool(getattr(sys, "frozen", False))


def open_output_file(output_path: Path) -> None:
    if os.name != "nt":
        return

    try:
        os.startfile(str(output_path))  # type: ignore[attr-defined]
    except OSError:
        pass


def collect_log_files(root: Path) -> list[Path]:
    files: list[Path] = []

    client_log = root / "client_log.txt"
    if client_log.exists():
        files.append(client_log)

    backup_client_logs = root / "backup" / "client_log"
    if backup_client_logs.exists():
        files.extend(backup_client_logs.glob("client_log_*.txt"))

    files.extend(root.rglob("server_log.txt"))

    seen: set[Path] = set()
    unique_files: list[Path] = []
    for f in files:
        resolved = f.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_files.append(f)

    return sorted(unique_files, key=lambda item: item.stat().st_mtime, reverse=True)


def extract_reports(log_file: Path) -> list[dict]:
    text = log_file.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    reports: list[dict] = []
    current: dict | None = None
    in_traceback = False

    for index, line in enumerate(lines):
        if BEGIN in line:
            current = {"file": log_file, "summary": {}, "traceback": [], "line_index": index}
            in_traceback = False
            continue

        if current is None:
            continue

        if END in line:
            current["line_index"] = index
            reports.append(current)
            current = None
            in_traceback = False
            continue

        if TRACEBACK_BEGIN in line:
            in_traceback = True
            continue

        if TRACEBACK_END in line:
            in_traceback = False
            continue

        if in_traceback:
            if line.startswith(TRACE_PREFIX):
                current["traceback"].append(line[len(TRACE_PREFIX) :])
            else:
                current["traceback"].append(line)
            continue

        if ERROR_PREFIX not in line:
            continue

        payload = line.split(ERROR_PREFIX, 1)[1]
        if "=" in payload:
            key, value = payload.split("=", 1)
            current["summary"][key.strip()] = value.strip()

    return reports


def detect_runtime(log_file: Path) -> tuple[str, str]:
    normalized = str(log_file).replace("\\", "/").lower()

    if "/backup/client_log/" in normalized or normalized.endswith("/client_log.txt"):
        return "客户端", "前端/客户端"

    if "/master/" in normalized:
        return "服务端", "Master"

    if "/caves/" in normalized:
        return "服务端", "Caves"

    return "未知", "未知"


def localize_prefab(value: str) -> str:
    if not has_value(value):
        return value

    return PREFAB_LABELS.get(value, value)


def localize_hook(value: str) -> str:
    if not has_value(value):
        return value

    return HOOK_LABELS.get(value, value)


def localize_action(value: str) -> str:
    if not has_value(value):
        return value

    return ACTION_LABELS.get(value, value)


def localize_event(value: str) -> str:
    if not has_value(value):
        return value

    return EVENT_LABELS.get(value, value)


def build_trigger_summary(action: str, event_name: str, target: str, actor: str) -> str:
    lowered_action = action.lower()
    lowered_event = event_name.lower()
    target_label = localize_prefab(target)
    actor_label = localize_prefab(actor)
    event_label = localize_event(event_name)

    if lowered_event == "picked" and target == "grass":
        if has_value(actor_label):
            return f"玩家 {actor_label} 采集{target_label}时触发"
        return f"采集{target_label}时触发"

    if lowered_event == "picked" and has_value(target):
        if has_value(actor_label):
            return f"玩家 {actor_label} 采集 {target_label} 时触发"
        return f"采集 {target_label} 时触发"

    if lowered_event == "attacked" and has_value(target):
        if has_value(actor_label):
            return f"玩家 {actor_label} 攻击 {target_label} 时触发"
        return f"攻击 {target_label} 时触发"

    if lowered_event == "equip" and has_value(target):
        if has_value(actor_label):
            return f"玩家 {actor_label} 装备 {target_label} 时触发"
        return f"装备 {target_label} 时触发"

    if lowered_event in ("builditem", "onbuilt") and has_value(target):
        if has_value(actor_label):
            return f"玩家 {actor_label} 制作或建造 {target_label} 时触发"
        return f"制作或建造 {target_label} 时触发"

    if "periodic" in lowered_action and has_value(target):
        return f"{target_label} 的周期任务触发"

    if "task_in_time" in lowered_action and has_value(target):
        return f"{target_label} 的延时任务触发"

    if "event_listener" in lowered_action and has_value(event_name):
        if has_value(target):
            return f"{target_label} 的事件 {event_label} 触发"
        return f"事件 {event_label} 触发"

    return "unknown"


def extract_trace_hint(traceback_lines: list[str]) -> tuple[str, str]:
    for line in traceback_lines:
        match = TRACE_FILE_RE.search(line)
        if match is not None:
            file_path = f"{match.group(1)}:{match.group(2)}"
            function_name = match.group(3)
            return file_path, function_name

        fallback_match = TRACE_FILE_RE_ALT.search(line)
        if fallback_match is not None:
            file_path = f"{fallback_match.group(1)}:{fallback_match.group(2)}"
            return file_path, "unknown"

    return "unknown", "unknown"


def normalize_reason(summary: dict, traceback_lines: list[str]) -> str:
    reason = summary.get("reason")
    if reason not in (None, "", "unknown"):
        return str(reason)

    for line in traceback_lines:
        stripped = line.strip()
        if stripped.startswith("../mods/") or stripped.startswith("[string "):
            continue
        if stripped:
            return stripped

    return "unknown"


def normalize_title(summary: dict) -> str:
    title = str(summary.get("title", "检测到 mod 异常"))
    if title == "native DST mod exception":
        return "检测到 DST 原生日志中的 mod 异常"
    return title


def normalize_capture_source(summary: dict) -> str:
    source = str(summary.get("source", "unknown"))
    if source == "client_log native parser":
        return "DST 原生日志解析"
    return "CrashTrace 结构化捕获"


def has_value(value: str) -> bool:
    return value not in ("", "unknown", "未知", "nil", "None")


def build_conclusion_lines(
    mod_id: str,
    mod_name: str,
    action: str,
    reason: str,
    suspect_file: str,
    runtime_side: str,
    runtime_scope: str,
    capture_source: str,
) -> list[str]:
    mod_label = mod_name if has_value(mod_name) else mod_id
    if not has_value(mod_label):
        mod_label = "未知 mod"

    lines = [
        "结论:",
        f"最可疑 mod: {mod_label}",
        f"触发位置: {runtime_side} / {runtime_scope}",
        f"捕获方式: {capture_source}",
    ]

    if has_value(action):
        lines.append(f"触发动作: {localize_action(action)}")

    if has_value(suspect_file):
        lines.append(f"优先检查: {suspect_file}")

    if has_value(reason):
        lines.append(f"核心原因: {reason}")

    return lines


def append_if_present(lines: list[str], label: str, value: str) -> None:
    if has_value(value):
        lines.append(f"{label}: {value}")


def build_suggestion_lines(
    runtime_side: str,
    runtime_scope: str,
    action: str,
    reason: str,
    suspect_file: str,
    suspect_function: str,
    capture_source: str,
) -> list[str]:
    suggestions = ["修复建议:"]

    if has_value(suspect_file):
        suggestions.append(f"先打开并检查: {suspect_file}")

    if runtime_side == "客户端":
        suggestions.append("这是客户端侧异常，优先检查客户端专属逻辑、界面逻辑和玩家生成相关回调。")
    elif runtime_side == "服务端":
        suggestions.append("这是服务端侧异常，优先检查世界逻辑、组件逻辑、任务调度和事件监听。")

    lowered_reason = reason.lower()
    lowered_action = action.lower()

    if "attempt to index" in lowered_reason and "nil value" in lowered_reason:
        suggestions.append("这类错误通常是对象为空后仍继续取字段，先检查变量判空和初始化顺序。")

    if "attempt to call" in lowered_reason and "nil value" in lowered_reason:
        suggestions.append("这类错误通常是函数不存在或当前环境不可用，先检查 API 是否在当前阶段可调用。")

    if "attempt to index field" in lowered_reason and "nil value" in lowered_reason:
        suggestions.append("这类错误通常是某个组件、字段或子对象不存在，先确认对象是否真的带有该字段。")

    if "prefabpostinit" in lowered_action:
        suggestions.append("当前报错发生在 prefab 初始化阶段，优先检查 PostInit 回调里是否访问了尚未准备好的对象。")

    if "playerpostinit" in lowered_action:
        suggestions.append("当前报错发生在玩家初始化阶段，优先检查玩家实体、组件和 replica 是否已经可用。")

    if action == "pick_action" or "picked" in lowered_reason or "picked" in lowered_action:
        suggestions.append("如果这是采集相关崩溃，优先检查 pickable、inventory、loot 结算以及采集事件回调。")

    if "attacked" in lowered_action or "attacked" in lowered_reason:
        suggestions.append("如果这是攻击相关崩溃，优先检查 combat、health、weapon 以及 attacked 事件参数。")

    if "equip" in lowered_action or "equip" in lowered_reason:
        suggestions.append("如果这是装备相关崩溃，优先检查 equippable、inventoryitem、owner 和装备栏状态。")

    if "build" in lowered_action or "builder" in lowered_reason:
        suggestions.append("如果这是建造相关崩溃，优先检查 builder、recipe、placer 和建造完成后的实体初始化。")

    if "onremove" in lowered_action or "onremove" in lowered_reason:
        suggestions.append("如果这是移除阶段崩溃，优先检查 OnRemoveEntity、事件解绑和周期任务清理。")

    if "death" in lowered_action or "death" in lowered_reason:
        suggestions.append("如果这是死亡阶段崩溃，优先检查 health 组件、死亡掉落和死亡事件监听。")

    if runtime_scope == "Caves":
        suggestions.append("当前发生在洞穴分片，确认洞穴分片独有 prefab、事件和世界组件是否存在。")

    if capture_source == "DST 原生日志解析":
        suggestions.append("这次是从 DST 原生日志反推出的异常，还不是 CrashTrace 自身的结构化捕获。")

    if has_value(suspect_function) and suspect_function != "unknown":
        suggestions.append(f"可重点检查函数: {suspect_function}")

    return suggestions


def format_report(report: dict) -> str:
    summary = report["summary"]
    traceback_lines = report["traceback"]
    runtime_side, runtime_scope = detect_runtime(report["file"])
    suspect_file, suspect_function = extract_trace_hint(traceback_lines)
    reason = normalize_reason(summary, traceback_lines)
    title = normalize_title(summary)
    capture_source = normalize_capture_source(summary)
    language = str(summary.get("language", "unknown"))
    version = str(summary.get("version", "unknown"))
    mod_id = str(summary.get("mod_id", "unknown"))
    mod_name = str(summary.get("mod_name", "unknown"))
    hook_type = str(summary.get("hook_type", "unknown"))
    action = str(summary.get("action", "unknown"))
    hook_label = str(summary.get("hook_label", "unknown"))
    action_label = str(summary.get("action_label", "unknown"))
    target = str(summary.get("target", "unknown"))
    prefab = str(summary.get("prefab", "unknown"))
    target_label = str(summary.get("target_label", "unknown"))
    prefab_label = str(summary.get("prefab_label", "unknown"))
    guid = str(summary.get("guid", "unknown"))
    event_name = str(summary.get("event", "unknown"))
    event_label = str(summary.get("event_label", "unknown"))
    actor = str(summary.get("picker", "unknown"))
    actor_label = str(summary.get("picker_label", "unknown"))
    trigger_summary = build_trigger_summary(action, event_name, target if has_value(target) else prefab, actor)
    suspect_function = str(suspect_function)
    suspect_file = str(suspect_file)
    suggestion_lines = build_suggestion_lines(
        runtime_side,
        runtime_scope,
        action,
        reason,
        suspect_file,
        suspect_function,
        capture_source,
    )

    lines = ["=== CrashTrace 最近一次诊断 ===", ""]
    lines.extend(
        build_conclusion_lines(
            mod_id,
            mod_name,
            action,
            reason,
            suspect_file,
            runtime_side,
            runtime_scope,
            capture_source,
        )
    )
    lines.extend(["", "摘要:", f"标题: {title}"])
    append_if_present(lines, "运行侧", runtime_side)
    append_if_present(lines, "范围", runtime_scope)
    append_if_present(lines, "语言", language)
    append_if_present(lines, "版本", version)
    append_if_present(lines, "Mod ID", mod_id)
    append_if_present(lines, "Mod 名称", mod_name)
    append_if_present(lines, "Hook 类型", hook_label if has_value(hook_label) else localize_hook(hook_type))
    append_if_present(lines, "原始 Hook", hook_type)
    append_if_present(lines, "触发动作", action_label if has_value(action_label) else localize_action(action))
    append_if_present(lines, "原始动作", action)
    append_if_present(lines, "触发事件", event_label if has_value(event_label) else localize_event(event_name))
    append_if_present(lines, "原始事件", event_name)
    append_if_present(lines, "触发者", actor_label if has_value(actor_label) else localize_prefab(actor))
    append_if_present(lines, "触发摘要", trigger_summary)
    append_if_present(lines, "目标对象", target_label if has_value(target_label) else localize_prefab(target))
    append_if_present(lines, "原始目标", target)
    append_if_present(lines, "Prefab", prefab_label if has_value(prefab_label) else localize_prefab(prefab))
    append_if_present(lines, "原始 Prefab", prefab)
    append_if_present(lines, "GUID", guid)
    append_if_present(lines, "错误原因", reason)
    append_if_present(lines, "疑似出错文件", suspect_file)
    append_if_present(lines, "疑似函数", suspect_function)
    lines.append(f"日志来源: {report['file']}")
    lines.append(f"捕获方式: {capture_source}")
    lines.extend([""])
    lines.extend(suggestion_lines)
    lines.extend(["", "调用栈:"])

    if traceback_lines:
        lines.extend(traceback_lines)
    else:
        lines.append("未找到 traceback。")

    return "\n".join(lines)


def write_output(output_path: Path, text: str) -> None:
    output_path.write_text(text, encoding="utf-8")


def extract_native_reports(log_file: Path) -> list[dict]:
    text = log_file.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    reports: list[dict] = []
    current: dict | None = None
    collecting_traceback = False

    for index, line in enumerate(lines):
        if "error calling " in line and " in mod " in line and "(" in line and "):" in line:
            payload = line.split("error calling ", 1)[1]
            action_part, mod_part = payload.split(" in mod ", 1)
            mod_id_part, mod_name_part = mod_part.split("(", 1)
            mod_name = mod_name_part.rsplit("):", 1)[0]
            current = {
                "file": log_file,
                "line_index": index,
                "summary": {
                    "title": "native DST mod exception",
                    "action": action_part.strip(),
                    "mod_id": mod_id_part.strip(),
                    "mod_name": mod_name.strip(),
                    "hook_type": action_part.strip(),
                    "target": "unknown",
                    "prefab": "unknown",
                    "guid": "unknown",
                    "source": "client_log native parser",
                },
                "traceback": [],
            }
            collecting_traceback = False
            continue

        if current is None and "../mods/" in line and "attempt to " in line and "[CrashTrace]" not in line:
            mod_match = MOD_SOURCE_RE.search(line)
            mod_id = mod_match.group(1) if mod_match is not None else "unknown"
            current = {
                "file": log_file,
                "line_index": index,
                "summary": {
                    "title": "native DST mod exception",
                    "action": "native_lua_error",
                    "mod_id": mod_id,
                    "mod_name": mod_id,
                    "hook_type": "native_lua_error",
                    "target": "unknown",
                    "prefab": "unknown",
                    "guid": "unknown",
                    "source": "client_log native parser",
                    "reason": line.strip(),
                },
                "traceback": [],
            }
            continue

        if current is None:
            continue

        if current["summary"].get("reason") is None:
            stripped = line.strip()
            if stripped and not stripped.startswith("[") and "LUA ERROR stack traceback:" not in stripped:
                current["summary"]["reason"] = stripped
                continue

        stripped = line.strip()
        if stripped.startswith("event = ") and current["summary"].get("event") is None:
            current["summary"]["event"] = stripped.split("=", 1)[1].strip()
            continue

        if " - " in stripped and "(valid:true)" in stripped and current["summary"].get("target") in (None, "unknown"):
            if stripped.startswith("grass = "):
                current["summary"]["target"] = "grass"
                current["summary"]["prefab"] = "grass"
                continue

        if "picker = " in stripped and "(valid:true)" in stripped and current["summary"].get("picker") is None:
            current["summary"]["picker"] = stripped.split(" - ", 1)[1].split(" ", 1)[0].strip()
            continue

        if stripped.startswith("attacker = ") and "(valid:true)" in stripped and current["summary"].get("picker") is None:
            current["summary"]["picker"] = stripped.split(" - ", 1)[1].split(" ", 1)[0].strip()
            current["summary"]["action"] = "attack_action"
            if not has_value(current["summary"].get("event", "unknown")):
                current["summary"]["event"] = "attacked"
            continue

        if stripped.startswith("target = ") and "(valid:true)" in stripped and current["summary"].get("target") in (None, "unknown"):
            current["summary"]["target"] = stripped.split(" - ", 1)[1].split(" ", 1)[0].strip()
            continue

        if stripped.startswith("item = ") and "(valid:true)" in stripped and current["summary"].get("target") in (None, "unknown"):
            current["summary"]["target"] = stripped.split(" - ", 1)[1].split(" ", 1)[0].strip()
            current["summary"]["action"] = "equip_action"
            if not has_value(current["summary"].get("event", "unknown")):
                current["summary"]["event"] = "equip"
            continue

        if stripped.startswith("builder = ") and "(valid:true)" in stripped and current["summary"].get("picker") is None:
            current["summary"]["picker"] = stripped.split(" - ", 1)[1].split(" ", 1)[0].strip()
            current["summary"]["action"] = "build_action"
            if not has_value(current["summary"].get("event", "unknown")):
                current["summary"]["event"] = "builditem"
            continue

        if stripped.startswith("recipe = ") and current["summary"].get("target") in (None, "unknown"):
            current["summary"]["target"] = stripped.split("=", 1)[1].strip()
            current["summary"]["action"] = "build_action"
            if not has_value(current["summary"].get("event", "unknown")):
                current["summary"]["event"] = "builditem"
            continue

        if "LUA ERROR stack traceback:" in line:
            collecting_traceback = True
            continue

        if collecting_traceback:
            if line.startswith("[") and "]: " in line:
                current["line_index"] = index
                reports.append(current)
                current = None
                collecting_traceback = False
                continue

            current["traceback"].append(line)
            continue

        if stripped.startswith("grass = ") and "(valid:true)" in stripped:
            current["summary"]["target"] = "grass"
            current["summary"]["prefab"] = "grass"
            continue

        if stripped.startswith("picker = ") and "(valid:true)" in stripped:
            current["summary"]["picker"] = stripped.split(" - ", 1)[1].split(" ", 1)[0].strip()
            continue

        if stripped.startswith("attacker = ") and "(valid:true)" in stripped:
            current["summary"]["picker"] = stripped.split(" - ", 1)[1].split(" ", 1)[0].strip()
            current["summary"]["action"] = "attack_action"
            if not has_value(current["summary"].get("event", "unknown")):
                current["summary"]["event"] = "attacked"
            continue

        if stripped.startswith("target = ") and "(valid:true)" in stripped:
            current["summary"]["target"] = stripped.split(" - ", 1)[1].split(" ", 1)[0].strip()
            continue

        if stripped.startswith("item = ") and "(valid:true)" in stripped:
            current["summary"]["target"] = stripped.split(" - ", 1)[1].split(" ", 1)[0].strip()
            current["summary"]["action"] = "equip_action"
            if not has_value(current["summary"].get("event", "unknown")):
                current["summary"]["event"] = "equip"
            continue

        if stripped.startswith("builder = ") and "(valid:true)" in stripped:
            current["summary"]["picker"] = stripped.split(" - ", 1)[1].split(" ", 1)[0].strip()
            current["summary"]["action"] = "build_action"
            if not has_value(current["summary"].get("event", "unknown")):
                current["summary"]["event"] = "builditem"
            continue

        if stripped.startswith("recipe = "):
            current["summary"]["target"] = stripped.split("=", 1)[1].strip()
            current["summary"]["action"] = "build_action"
            if not has_value(current["summary"].get("event", "unknown")):
                current["summary"]["event"] = "builditem"
            continue

        if "Disabling " in line and " because it had an error." in line and "(" in line and ")" in line:
            payload = line.split("Disabling ", 1)[1]
            mod_id_part, mod_name_part = payload.split("(", 1)
            current["summary"]["mod_id"] = mod_id_part.strip()
            current["summary"]["mod_name"] = mod_name_part.split(")", 1)[0].strip()
            continue

        if current["summary"].get("reason") is None and ("attempt to " in line or "[string " in line or ".lua" in line):
            if "]: " in line:
                payload = line.split("]: ", 1)[1]
            else:
                payload = line
            current["summary"]["reason"] = payload.strip()

        if "scripts/components/pickable.lua" in line:
            current["summary"]["action"] = "pick_action"
            if not has_value(current["summary"].get("event", "unknown")):
                current["summary"]["event"] = "picked"

        if "scripts/components/combat.lua" in line:
            current["summary"]["action"] = "attack_action"
            if not has_value(current["summary"].get("event", "unknown")):
                current["summary"]["event"] = "attacked"

        if "scripts/components/equippable.lua" in line or "scripts/components/inventoryitem.lua" in line:
            current["summary"]["action"] = "equip_action"
            if not has_value(current["summary"].get("event", "unknown")):
                current["summary"]["event"] = "equip"

        if "scripts/components/builder.lua" in line or "scripts/recipes.lua" in line:
            current["summary"]["action"] = "build_action"
            if not has_value(current["summary"].get("event", "unknown")):
                current["summary"]["event"] = "builditem"

    if current is not None:
        reports.append(current)

    return reports


def collect_reports_for_file(log_file: Path) -> list[dict]:
    reports = []
    reports.extend(extract_reports(log_file))
    reports.extend(extract_native_reports(log_file))
    return reports


def main() -> int:
    args = parse_args()
    root = resolve_root_path(args.root)
    output_path = resolve_output_path(args.output)

    if not root.exists():
        message = "\n".join(
            [
                "未找到 DST 日志目录。",
                f"日志目录: {root}",
                "请先启动一次 DST，或通过 --root 指定日志目录。",
            ]
        )
        print(message)
        write_output(output_path, message + "\n")
        if should_open_output(args):
            open_output_file(output_path)
        return 1

    log_files = collect_log_files(root)
    if not log_files:
        message = "\n".join(
            [
                "未找到 client_log.txt 或 server_log.txt。",
                f"日志目录: {root}",
                "请先启动一次 DST，并确认日志目录没有被清理。",
                f"独立服务器目录: {', '.join(DEDICATED_SERVER_DIRS)}",
            ]
        )
        print(message)
        write_output(output_path, message + "\n")
        if should_open_output(args):
            open_output_file(output_path)
        return 1

    all_reports: list[tuple[float, int, dict]] = []
    for log_file in log_files:
        file_mtime = log_file.stat().st_mtime
        reports = collect_reports_for_file(log_file)
        for report in reports:
            line_index = report.get("line_index", -1)
            all_reports.append((file_mtime, line_index, report))

    if all_reports:
        all_reports.sort(key=lambda item: (item[0], item[1]), reverse=True)
        latest_report = all_reports[0][2]
        text = format_report(latest_report)
        print(text)
        write_output(output_path, text + "\n")
        if should_open_output(args):
            open_output_file(output_path)
        return 0

    text = "\n".join(
        [
            f"{APP_NAME} 未在 DST 日志中找到可用报告。",
            "请确认已经启用 `dst-mod-crash-tracer` 并实际触发过一次 mod 异常。",
            f"当前扫描目录: {root}",
            "如果本次崩溃非常早，也可能只有 DST 原生日志，没有结构化 CrashTrace 报告。",
        ]
    )
    print(text)
    write_output(output_path, text + "\n")
    if should_open_output(args):
        open_output_file(output_path)
    return 1


if __name__ == "__main__":
    sys.exit(main())
