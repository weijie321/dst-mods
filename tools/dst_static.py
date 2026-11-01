"""只检查可证明的 Lua 声明和资源路径，不执行模组代码。"""
from pathlib import Path, PurePosixPath
import re
import zipfile


def check_resources(mod: Path, dst: Path) -> dict:
    from luaparser import ast, astnodes as n

    errors, reviews, resources = [], [], []
    metadata = {}
    invalid_metadata = set()
    for required in ("modinfo.lua", "modmain.lua"):
        if not (mod / required).is_file():
            errors.append(f"缺少 {required}")
    archive = dst / "data/databundles/scripts.zip"
    with zipfile.ZipFile(archive) as z:
        members = set(z.namelist())
        constants = z.read("scripts/mods.lua").decode("utf-8-sig")
    version = re.search(r"\bMOD_API_VERSION\s*=\s*(\d+)", constants)

    def string(node):
        if isinstance(node, n.String):
            return node.s.decode("utf-8") if isinstance(node.s, bytes) else node.s
        return None

    def resource(value, owner, local_only=False):
        value = value.replace("\\", "/")
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or ":" in value:
            errors.append(f"{owner}: 资源路径越界 {value}")
            return
        found = (mod / value).is_file()
        if not local_only:
            found |= (dst / "data" / value).is_file() or value in members
        resources.append({"source": owner, "path": value, "found": found})
        if not found:
            errors.append(f"{owner}: 找不到资源 {value}")

    for path in sorted(mod.rglob("*.lua")):
        relative = path.relative_to(mod).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            errors.append(f"{relative}: Lua 无法解析: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, n.Assign):
                for target, value in zip(node.targets, node.values):
                    if not isinstance(target, n.Name):
                        continue
                    if relative == "modinfo.lua":
                        metadata[target.id] = string(value) if isinstance(value, n.String) else getattr(value, "n", getattr(value, "value", None))
                        if target.id in ("name", "description", "author", "version"):
                            if isinstance(value, (n.Nil, n.TrueExpr, n.FalseExpr, n.Number, n.Table)) or (isinstance(value, n.String) and not string(value).strip()):
                                invalid_metadata.add(target.id)
                        if isinstance(value, n.TrueExpr):
                            metadata[target.id] = True
                        elif isinstance(value, n.FalseExpr):
                            metadata[target.id] = False
                    if target.id == "PrefabFiles":
                        if not isinstance(value, n.Table):
                            reviews.append(f"{relative}: 动态 PrefabFiles 需运行时验证")
                        else:
                            for field in value.fields:
                                name = string(field.value)
                                if name is None:
                                    reviews.append(f"{relative}: 动态 PrefabFiles 项需运行时验证")
                                else:
                                    resource(f"scripts/prefabs/{name}.lua", relative, True)
            if not isinstance(node, n.Call) or not isinstance(node.func, n.Name):
                continue
            api = node.func.id
            arg = 1 if api == "Asset" else 0
            if api not in ("Asset", "RegisterInventoryItemAtlas", "RegisterSkilltreeIconsAtlas",
                           "RegisterScrapbookIconAtlas", "AddMinimapAtlas", "modimport"):
                continue
            if len(node.args) <= arg:
                errors.append(f"{relative}: {api} 缺少路径参数")
                continue
            value = string(node.args[arg])
            if value is None:
                reviews.append(f"{relative}: {api} 动态路径需运行时验证")
            else:
                resource(value, relative, api == "modimport")
    for field in ("name", "description", "author", "version"):
        if field not in metadata:
            errors.append(f"modinfo.lua 未定义 {field}")
        elif field in invalid_metadata:
            errors.append(f"modinfo.lua 的 {field} 不能是空值或非字符串常量")
    api = metadata.get("api_version_dst", metadata.get("api_version"))
    if version and api != int(version.group(1)):
        errors.append(f"modinfo API {api} 与当前安装版本 {version.group(1)} 不一致")
    if metadata.get("dst_compatible") is not True:
        errors.append("modinfo.lua 需要 dst_compatible=true")
    if metadata.get("client_only_mod") is True and metadata.get("all_clients_require_mod") is True:
        errors.append("client_only_mod 和 all_clients_require_mod 冲突")
    return {"status": "failed" if errors else ("review_required" if reviews else "passed"),
            "errors": errors, "reviews": reviews, "resources": resources,
            "scope": "静态字符串资源、PrefabFiles 和 modinfo；动态资源不自动视为已验证"}
