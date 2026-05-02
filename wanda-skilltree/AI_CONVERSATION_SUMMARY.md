# 给后续 AI 的一页摘要（旺达技能树 Mod）

**项目**：`Don't Starve Together` 模组 **wanda-skilltree**，为旺达扩展官方式技能树（五栏：岁月 / 怀表 / 时空 / 团队 / 亲和），并 Hook 怀表、倒走、溯源、裂缝、警钟、时光贮匣等。

**根路径**：`dst-mods/wanda-skilltree/`。详细设计对照、文件表、续开发顺序见同目录 **`DEVELOPMENT_STATUS.md`**（以该文件为事实源，本摘要仅加速上下文加载）。

**必读入口**：`modmain.lua`（注册树、Prefab、配方、`modimport`）；`scripts/wanda_skill_hooks.lua`（主体逻辑）；`scripts/prefabs/skilltree_wanda.lua`（节点与连线）。`skilltree_wanda` 仅作 `Asset("SCRIPT", ...)` 加载，**不要**放进 `PrefabFiles`。

**已大致落地**：技能树注册与安全跳过（若官方已有 `wanda` 树）；旺达 PostInit（年龄上限、部分迟暮从容、位面相关 `planardefense`、配方 tag）；不老表团队治疗与短庇护；倒走加速、warp 首帧无敌、残影占位；溯源表绑定/存档/传送分支与 `WANDA_BOND_MARK`；裂缝表在「恒稳裂隙」下的自定义分支；怀表 `rechargeable:Discharge` 调校；警钟/绝望钟叠层与月亮 AOE（简化）；幽灵侧「命运回拨」雏形；时光贮匣三阶 + `EQUIPSLOTS.WANDA_TIMEBOX` + `inventorybar` 加槽；时间碎片与相关 `AddRecipe2`。

**已修复项**：① 逆龄余波已改用 `oldager:OnTakeDamage(bonus, false, "wanda_heal_bonus")`，注册 valid healing cause。② 恒稳裂隙已对齐原版 walkable offset + SpawnExit + 音效 + 冷却，保留裂缝表不消耗。③ 技能树 FLOATING 已确认为误报（connects 从父节点连通）。④ 贮匣栏 `CanEquipTimeBox` 校验技能后才允许装备。⑤ 技能激活 — 通过 `AddComponentPostInit("skilltreeupdater")` 初始化服务端+客户端 skillxp；`OnWandaPostInit` 事件监听 `onactivateskill_server` + `ms_skilltreeinitialized` 驱动 bonus 应用。移除类表级 ActivateSkill hook（2026-05-03 发现该 hook 会破坏所有角色技能激活）。⑥ `health` 组件仅服务端存在，数值修改函数已加 `TheWorld.ismastersim` 保护。⑦ `restart_required` 改为 false。⑧ 技能树布局：亲和改为左右两列竖向排列，迟暮从容加 `connects = {}`。⑨ `healthdelta` 事件直接调用 `ApplyOldCalm`，不创建 DoTaskInTime 延迟任务。

**剩余高优先级缺口**：① **岁月感知** 与原版 `wanda` + `oldager` 是否一致需对照原版 Lua。② **岁月主宰** 的 `planardefense:SetBaseDefense(0.5)` 是否等于「位面伤害减半」需查原版组件语义。③ **命运回拨**：复活优先级、`ms_becameghost` / `respawnfromghost` 是否合适、绑定表扫描范围。④ **钟表调校**：仅 Hook `rechargeable:Discharge`，未覆盖 `finiteuses`、`fueled` 等其它消耗路径。

**环境说明**：交接文档基于静态代码整理；**未**在本仓库环境内完整跑 DST 客户端验证。改代码后请同步更新 `DEVELOPMENT_STATUS.md` 第 2–3 节。

**用户偏好**：中文沟通；小改动可直接改仓库；大架构或大规模改动可先 plan 或与用户确认。UTF-8 保存 Lua/MD。
