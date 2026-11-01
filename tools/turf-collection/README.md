# 地皮抽取工具

仅处理用户点名的 11 个本地创意工坊副本，不修改来源文件，不下载或发布创意工坊内容。生成目标为工作区 `turf-collection/`。运行前按根目录 `AGENTS.md` 和 `tools/DST_TESTING.md` 执行 `doctor`，使用本机配置中的 Python、游戏目录与项目外证据目录。

需要已有的 Lua 5.4（`lua` 命令）、Python 3.10+；运行时模组本身不需要这些工具。

```text
python tools/turf-collection/extract.py --workshop-root <steamapps/workshop/content/322330> --evidence <项目外证据目录/capture>
python tools/turf-collection/build.py --workshop-root <steamapps/workshop/content/322330> --captured <项目外证据目录/capture/captured.json> --dst-root <游戏安装目录> --output turf-collection
python tools/turf-collection/validate.py --workshop-root <steamapps/workshop/content/322330> --dst-root <游戏安装目录> --mod turf-collection
```

`extract.py` 选择确切的地皮声明入口，在无系统命令能力的离线 Lua 环境中捕获 `AddTile` 参数。丰耘使用其加载器读取对应资料表，童话世界读取其编码后的独立地皮表；不把完整来源 Lua 纳入合集运行文件。中间声明与捕获 JSON 写到指定的项目外证据目录。

`build.py` 复制所需纹理、边缘遮罩、动画和图标；对自定义图集与地形命名加来源命名空间，复用共用图集纹理，生成中文目录和来源指纹。特殊平台/临时地形转为普通可铺挖地纹，悠使用其真实自定义物品动画契约。实际调整记录在 `SOURCES.json`。重建应在无手工修改的生成目标中执行。

`validate.py` 校验 11 个来源、130 项完整性、源文件指纹、全部本地资源与图集依赖，并直接读取 `ANIM/BILD` 验证 bank、build、animation 三者匹配。它不替代专服或真实客户端验收。

之后按 `check → test → verify` 完整验收；计划为 `tools/acceptance/turf-collection.json`。客户端夹具由客户端桥接器在本轮完成事件到达后结束，不能在准备好测试物品时提前 `TEST.Done`。部署遵守统一入口的成功完整 `verify` 报告门禁。
