# 321自用dp

无需启用来源模组，可独立使用的 DST 服务器模组。所有玩家都需要安装并启用。

当前版本 `0.1.4`，模组及制作分类显示名为“321自用dp”。已修复制作栏预览尺寸及三项图标来源，更新后重启游戏加载。工坊主封面已更换为抽象几何图并通过远程图片哈希核实，条目为 [3831552730](https://steamcommunity.com/sharedfiles/filedetails/?id=3831552730)。

手动安装时，把完整的 `turf-collection` 文件夹放入游戏安装目录的 `mods/`，确认目录内直接包含 `modinfo.lua` 和 `modmain.lua`。房主及每位联机玩家均需安装同一版本；专服也需安装并在对应分片的 `modoverrides.lua` 中启用 `turf-collection`。

本机源码工作区可双击 `tools/install_turf_collection.bat`。它读取本机开发配置中的 `deploy_dst_root`（未设置时使用 `dst_root`），先预览，再使用最近的成功验收报告通过统一入口复制到 `mods/turf-collection`；旧文件自动备份，复制后校验哈希。源码、游戏或验收工具变化导致报告失效时会停止，需重新 `verify`。客户端复制完成后重启游戏，在“创建世界 → 模组 → 服务器模组”中启用合集；独立专服须先停服，更新到验收版本再启动。脚本只同步模组文件，不改存档或启用配置。仅预览可运行 `pwsh -File tools/install_turf_collection.ps1 -Preview`；可用 `-ConfigPath <本机配置文件>` 指定其他配置。

在游戏内启用“321自用dp”后进入世界。制作栏有独立的“321自用dp”分类；所有角色无需科技即可用 **1 草 + 1 石头制作 4 块**。物品名称采用“来源模组·地皮名称”，可以搜索。使用方式与原版地皮一致：铺在已挖净的地面上，用草叉挖回。

| 来源 | 收录注册地皮数 |
| --- | ---: |
| 海洋传说 | 11 |
| 荔只只 | 23 |
| 丰耘秘境 | 5 |
| 童话世界 | 15 |
| 万物书 | 26 |
| 景熹家居 | 14 |
| 田园物语 | 1 |
| 花仙子 | 12 |
| 新版樱花林 | 9 |
| 炊烟袅袅 | 11 |
| 悠 | 3 |
| **合计** | **130** |

桥梁基底、码头、睡莲平台、裂隙等支持地形以“普通陆地地纹”形式收录。荔只只的 7 种桥基底原本共用藤蔓地纹，桥的视觉结构是实体动画；合集中的基底地纹不生成桥、不填海，也不提供平台功能。特殊地形变为可铺挖，不带入原模组的生物、角色、世界生成、商店和其他玩法。原有地板、硬地面、道路加速标记保留；樱花林自定义脚步声换为原版草地脚步声。部分支持地形没有普通地皮物品，使用原版地皮动画和对应地纹预览图标。

收录依据为来源副本中的真实地皮注册声明；未注册测试贴图、建筑类实体地毯和皮肤不计入地皮数量。已有来源模组铺下的地皮不会自动变为合集地皮。卸载合集前应先挖回合集中铺下的地皮。

地皮、物品和自定义地纹使用独立命名，但动画仍保留来源的 bank/build 内部名称。同名且内容一致的资源通常可以共用；原模组更新或同名资源内容不同时，仍可能发生贴图、动画冲突。与原 11 个模组同时启用尚未验收；已有存档不要因安装合集就直接停用提供原有地皮的模组。本地版与创意工坊版也应避免同时启用。

## 创意工坊发布与更新

从 Steam“工具”启动官方 Don't Starve Mod Tools 的 `ModUploader.exe`，目标游戏选择 Don't Starve Together。上传目录选择包含 `modinfo.lua` 的模组文件夹；后续更新选择已有条目，避免重复创建。合集的工坊条目及当前可见性统一见 [开发状态](DEVELOPMENT_STATUS.md)。

本机上传文件集中放在项目根目录的 `workshop-upload/`：上传内容选择其中的 `turf-collection/`，封面单独选择旁边的 `turf-collection-preview.jpg`。该目录是已验收版本的上传副本，更新版本时需重新同步并校验；不包含测试日志，也不纳入 Git。

上传器的预览图需单独选择有效图片。本机交付封面为 `evidence_root/dist/turf-collection-preview.jpg`，已检查为 RGB JPEG、512×512、约 25 KB，内容是与游戏无关的抽象几何图。上传条目标题填写“321自用dp”。封面建议保存在模组目录外，避免后续严格同步运行文件时作为额外文件清除。上传后在工坊网页核对标题与说明；上传器显示乱码时，不能直接认定网页标题正确。

SteamCMD 可使用 `workshop_build_item <VDF绝对路径>` 更新原条目。工坊网页的 `version:...` 标签与模组内版本是独立元数据，SteamCMD 不会依据 `modinfo.lua` 自动同步该标签。VDF 的 `publishedfileid` 固定为 `3831552730`，`appid` 为 `322330`，`contentfolder` 指向上传文件夹，`previewfile` 指向外部封面；省略 `visibility` 保留现有权限。密码和验证码只在 SteamCMD 本机交互输入，不放入命令、VDF 或文档。登录缓存由 SteamCMD 自身管理，不复制 Steam 客户端 token。

上传后用官方匿名接口核对实际结果：向 `https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/` 发送 POST，表单为 `itemcount=1`、`publishedfileids[0]=3831552730`；检查 `title`、`visibility`、`time_updated`、`preview_url`，封面还需核对返回图片。该接口已验证可用，不需 API key，但不提供已验证的作者侧待审核诊断。网页访问仅作为页面提示的补充；需要作者登录的提示仍待核查。不能只凭 `Success` 宣称生效，当前核实结果统一见开发状态。

若官方上传器报 `Error updating item`，先看 Steam 安装目录的 `logs/workshop_log.txt`。本机此次 `Getting Workshop info ... File Not Found` 实为桌面 Steam 会话断开：界面底部显示“无连接”，`ISteamUser::BLoggedOn()` 返回 `false`；恢复在线后上传与主封面替换成功。先退出 SteamCMD、保存并退出正在运行的游戏，再完整退出并重新登录桌面 Steam，确认“无连接”消失后重开上传器；只重开上传器无法恢复 Steam 会话。网页仍能访问、界面仍显示用户名，不等于 Steam API 在线。其他错误应根据新日志排查，勿把所有 `File Not Found` 都判为同一原因。

“仅好友”“隐藏”和“不公开”是不同权限：仅好友/隐藏条目不会作为普通公开条目出现在搜索中，访问和下载受权限限制，不能据此保证陌生玩家或匿名专服可自动下载。如果只是不希望被搜索且上传器提供 Unlisted，应单独验证目标玩家和专服的访问、订阅与下载。公开后也需要等待 Steam 搜索收录。

上传前核对来源作者的转载、整合许可，并在工坊说明保留来源。工坊上传或更改可见性不由本地复制脚本自动执行。

完整清单见 [TURFS.md](TURFS.md)，当前验收边界见 [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md)。来源链接、声明文件、资源指纹和逐项调整记录在 [SOURCES.json](SOURCES.json)。原贴图及动画归对应模组作者所有，合集仅做资源整理与独立注册。

开发、测试与部署使用仓库根目录 `tools/DST_TESTING.md` 中的统一入口。生成脚本在 `tools/turf-collection/`，只读来源副本，解包中间文件与测试证据留在配置的 `evidence_root`。
