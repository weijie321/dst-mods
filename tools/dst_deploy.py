"""预览或部署单个本地模组；修改前备份，完成后按内容哈希核对。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".codex", ".omc",
    ".venv", "venv", "__pycache__", ".pytest_cache", "docs", "tests",
    "test", "test-reports", "reports", "logs", "source_art", "raw_assets", "exported",
}
EXCLUDED_SUFFIXES = {
    ".md", ".py", ".pyc", ".ps1", ".bat", ".log", ".psd", ".scml",
    ".scon", ".kra", ".xcf", ".ase", ".aseprite", ".blend",
}


class DeployError(RuntimeError):
    """部署未完成；异常消息包含已有备份和回滚状态。"""


def _is_link(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


def _no_links(path: Path) -> None:
    for item in (path, *path.parents):
        if os.path.lexists(item) and _is_link(item):
            raise DeployError(f"不允许符号链接或目录联接：{item}")


def _overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _skip(relative: Path) -> bool:
    name = relative.name.lower()
    return (
        any(part.lower() in EXCLUDED_DIRS or part.startswith(".") for part in relative.parts)
        or relative.suffix.lower() in EXCLUDED_SUFFIXES
        or name == "dst_selftest.lua"
        or name.startswith(("readme", "selftest-", "selftest_", "latest_crashtrace_report"))
        or name.endswith("-report.json")
    )


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _walk_error(error: OSError) -> None:
    raise error


def _inventory(root: Path, *, source: bool = False) -> dict[str, str]:
    _no_links(root)
    if not root.exists():
        return {}
    if not root.is_dir():
        raise DeployError(f"路径不是目录：{root}")
    files = {}
    for current, dirs, names in os.walk(root, followlinks=False, onerror=_walk_error):
        current_path = Path(current)
        for name in list(dirs):
            item = current_path / name
            relative = item.relative_to(root)
            if _is_link(item):
                raise DeployError(f"不允许符号链接或目录联接：{item}")
            if source and _skip(relative):
                dirs.remove(name)
        for name in names:
            item = current_path / name
            if _is_link(item) or not item.is_file() or (not source and item.stat().st_nlink > 1):
                raise DeployError(f"不允许链接或非常规文件：{item}")
            relative = item.relative_to(root)
            if not source or not _skip(relative):
                files[relative.as_posix()] = _hash(item)
    return dict(sorted(files.items()))


def _paths(workspace: Path, dst_root: Path, mod: str, evidence_root: Path) -> tuple[Path, Path, Path]:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", mod) or mod.lower().startswith("workshop-"):
        raise DeployError("模组名必须是工作区直属本地模组名，不能是路径或 Workshop 条目")
    workspace, dst_root, evidence_root = (
        Path(item).expanduser().absolute() for item in (workspace, dst_root, evidence_root)
    )
    for item in (workspace, dst_root, evidence_root):
        _no_links(item)
    workspace, dst_root, evidence_root = (item.resolve() for item in (workspace, dst_root, evidence_root))
    if _overlap(workspace, dst_root) or _overlap(evidence_root, workspace) or _overlap(evidence_root, dst_root):
        raise DeployError("工作区、游戏目录、证据目录必须相互独立，不能互相嵌套")
    source = workspace / mod
    target = dst_root / "mods" / mod
    _no_links(source)
    _no_links(target)
    if not (dst_root / "mods").is_dir():
        raise DeployError(f"游戏 mods 目录不存在：{dst_root / 'mods'}")
    if not source.is_dir() or not all((source / name).is_file() for name in ("modinfo.lua", "modmain.lua")):
        raise DeployError(f"不是工作区直属的已知模组（缺少 modinfo.lua/modmain.lua）：{source}")
    if (target / ".git").exists():
        raise DeployError(f"目标是 Git 工作副本，不能作为部署目录：{target}")
    return source, target, evidence_root


def runtime_manifest(root: Path) -> dict[str, str]:
    """返回实际部署集合的 SHA-256，沿用部署的过滤与链接检查。"""
    return _inventory(Path(root), source=True)


def plan_deploy(workspace: Path, dst_root: Path, mod: str, evidence_root: Path) -> dict:
    """只读列出将部署的文件、目标差异及 SHA-256，不创建任何目录。"""
    source, target, evidence_root = _paths(workspace, dst_root, mod, evidence_root)
    expected = runtime_manifest(source)
    previous = _inventory(target)
    return {
        "status": "preview", "mod": mod, "source": str(source), "target": str(target),
        "evidence_root": str(evidence_root), "expected": expected, "previous": previous,
        "changes": {
            "add": sorted(expected.keys() - previous.keys()),
            "update": sorted(name for name in expected.keys() & previous.keys() if expected[name] != previous[name]),
            "delete": sorted(previous.keys() - expected.keys()),
            "unchanged": sum(expected[name] == previous[name] for name in expected.keys() & previous.keys()),
        },
        "hash_verify": None, "backup_dir": None,
    }


def _save_manifest(backup: Path, manifest: dict) -> None:
    pending = backup / "manifest.pending.json"
    pending.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending.replace(backup / "manifest.json")


def _remove_empty_dirs(root: Path, keep: set[Path]) -> None:
    if not root.exists():
        return
    for current, _, _ in os.walk(root, topdown=False, followlinks=False, onerror=_walk_error):
        path = Path(current)
        if path not in keep and not any(path.iterdir()):
            path.rmdir()


def deploy_mod(workspace: Path, dst_root: Path, mod: str, evidence_root: Path, *, apply: bool = False) -> dict:
    """默认预览；apply 时保留差异备份，失败自动恢复，成功核对完整运行文件集合。"""
    plan = plan_deploy(workspace, dst_root, mod, evidence_root)
    if not apply:
        return plan
    changed = plan["changes"]
    if not any(changed[key] for key in ("add", "update", "delete")):
        plan.update(status="unchanged", hash_verify=True)
        return plan

    source, target = Path(plan["source"]), Path(plan["target"])
    backup = Path(plan["evidence_root"]) / "deploy" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:12])
    _no_links(backup)
    backup.mkdir(parents=True, exist_ok=False)
    plan["backup_dir"] = str(backup)
    plan["status"] = "preparing"
    _save_manifest(backup, plan)
    original_dirs = {Path(current) for current, _, _ in os.walk(target, followlinks=False)}
    try:
        for name in changed["update"] + changed["delete"]:
            destination = backup / "before" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target / name, destination)
            if _hash(destination) != plan["previous"][name]:
                raise DeployError(f"备份期间目标内容发生变化：{name}")
        for name in changed["add"] + changed["update"]:
            destination = backup / "staged" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / name, destination)
            if _hash(destination) != plan["expected"][name]:
                raise DeployError(f"准备期间源码发生变化：{name}")
        if _inventory(target) != plan["previous"] or _inventory(source, source=True) != plan["expected"]:
            raise DeployError("准备期间源码或目标发生变化，请重新预览")
    except Exception as exc:
        plan.update(status="prepare_failed", error=str(exc))
        _save_manifest(backup, plan)
        raise DeployError(f"部署准备失败，游戏目录未改动；证据：{backup}；{exc}") from exc

    try:
        # 先删除已列出且已备份的旧文件，兼容文件与子目录相互替换。
        for name in changed["delete"]:
            _no_links(target / name)
            (target / name).unlink()
        _remove_empty_dirs(target, {target})
        for name in changed["add"] + changed["update"]:
            destination = target / name
            _no_links(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup / "staged" / name, destination)
        if _inventory(target) != plan["expected"]:
            raise DeployError("部署后文件集合或 SHA-256 不匹配")
        plan.update(status="applied", hash_verify=True)
        _save_manifest(backup, plan)
    except Exception as exc:
        try:
            _no_links(target)
            for name in changed["add"]:
                destination = target / name
                _no_links(destination)
                if destination.is_file():
                    destination.unlink()
            _remove_empty_dirs(target, original_dirs)
            for name in changed["update"] + changed["delete"]:
                destination = target / name
                _no_links(destination)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup / "before" / name, destination)
            for directory in original_dirs:
                _no_links(directory)
                directory.mkdir(parents=True, exist_ok=True)
            if _inventory(target) != plan["previous"]:
                raise DeployError("回滚后哈希不匹配")
            plan.update(status="rolled_back", hash_verify=False, error=str(exc))
        except Exception as rollback_error:
            plan.update(status="rollback_failed", hash_verify=False, error=str(exc), rollback_error=str(rollback_error))
        try:
            _save_manifest(backup, plan)
        except OSError:
            pass  # 首次写入的清单和 before 备份仍保留；异常信息包含实际回滚状态。
        raise DeployError(f"部署失败，状态 {plan['status']}；备份：{backup}；{exc}") from exc

    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--dst-root", type=Path, required=True)
    parser.add_argument("--mod", required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="应用预览中的变更；默认仅预览")
    args = parser.parse_args()
    try:
        result = deploy_mod(args.workspace, args.dst_root, args.mod, args.evidence_root, apply=args.apply)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (DeployError, OSError) as exc:
        print(f"部署失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
