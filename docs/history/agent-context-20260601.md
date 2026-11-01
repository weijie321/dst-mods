<claude-mem-context>
# Memory Context

# [dst-mods] recent context, 2026-06-01 11:08pm GMT+8

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (16,885t read) | 0t work

### May 2, 2026
S4 Diagnosing claude-mem "Failed to start worker" error on Windows — root cause identified (May 2, 7:20 PM)
S5 调试旺达(Wanda)年龄条显示"Max:80"的bug，追踪max health值在DST引擎中的传递路径 (May 2, 7:24 PM)
24 8:43p 🔵 oldager.lua component API fully discovered - critical for reverse aging fix
30 " 🔵 Vanilla pocketwatch system architecture fully mapped
32 " 🔵 Don't Starve Mod: Wanda Age Bar Max Value Bug Persists
27 " 🔵 Vanilla pocketwatch heal implementation inside pocketwatch.lua prefab
29 " 🔵 VANILLA heal watch ALSO uses health:DoDelta - mod's approach is CORRECT
31 8:44p ⚖️ Development tasks created: heal fix, timebox slot, portal alignment
34 11:41p 🔵 DST Health Component: Max Health Setter Syncs to Replica
35 " 🔵 DST Health:SetMaxHealth Resets Current Health to Max
36 " 🔴 Wanda Mod: Enhanced Debug Logging for Age Max Replica Sync
33 " 🔵 DST Source: Health Replica Max Fallback Value is 100
37 " ✅ Wanda Skill Mod: Deployed Enhanced Debug Build to Game Directory
S6 调试旺达年龄条"Max:80"bug：增强ApplyAgeMax日志以追踪replica同步 (May 2, 11:42 PM)
S7 调试旺达年龄条"Max:80"：部署replica同步验证日志，等待游戏内测试 (May 2, 11:43 PM)
S8 调试旺达年龄条"Max:80"bug - 等待游戏内replica同步测试结果 (May 2, 11:43 PM)
S9 调试旺达年龄条"Max:80"bug - 部署完成等待游戏测试 (May 2, 11:43 PM)
S10 调试旺达年龄条"Max:80"bug - 等待游戏测试反馈 (May 2, 11:44 PM)
S11 调试旺达年龄条"Max:80"bug + 同步项目文档和记忆 (May 2, 11:44 PM)
39 11:45p 🔵 DST Mod Project: Crash Tracer Mod Architecture Documented
38 " 🔵 DST Mod Project: Existing Memory Index Contains Key Pitfalls
40 11:47p 🔵 DST Mod Pitfalls: MaxHealth Sync Bug Already Documented as Known Issue
41 " 🔵 Wanda Skilltree Mod: Project Docs Include Development Status
42 11:48p 🔵 Wanda Skilltree Dev Status: ApplyAgeMax Approach May Be Fundamentally Wrong
43 11:49p 🔵 DST Mods Workspace: CLAUDE.md Documents Full Project Layout and Log Paths
44 11:50p ✅ CLAUDE.md Updated: Added wanda-skilltree to Project Structure
45 " ✅ DST Mod Pitfalls Updated: MaxHealth Sync Chain Documented with Hypotheses
46 " 🔵 Wanda Age Max Bug: Server Logs Confirm maxage 60→100 But Client Shows Max:80
47 " 🔵 Wanda Skilltree: Previously Fixed Items Documented in AI Conversation Summary
48 11:52p 🔵 Wanda Skilltree: Full AI Conversation Summary Reveals Top Priority Gaps
49 11:55p 🔴 Untitled
S12 调试旺达年龄条Max:80 - 服务端日志确认sync正常，发现health_replica.lua中有penalty计算 (May 2, 11:55 PM)
50 11:56p 🔵 Server Logs: replica.Max() Returns 150 - Sync Working, Max:80 Source Unknown
S13 调试旺达年龄条"Max:80"bug - 服务端日志分析与health_replica penalty发现 (May 2, 11:58 PM)
51 11:59p 🔵 Health Widget Search: No Direct maxhealth References in Widget Files
### May 3, 2026
52 12:00a 🔵 Critical Find: wandaagebadge.lua Uses health:Max() for Age Bar Display
53 12:03a 🔵 Client-side display error persists after user interaction
55 12:04a ✅ Wanda skill tree mod synced to game directory for testing
56 12:06a 🔵 WandaSkill server-side maxhealth correctly set to 150
57 " 🔵 DST player_classified.lua maxhealth network variable architecture
54 12:08a 🔵 DST maxhealth networking traced in original source
58 12:09a 🔵 DST SetValue and SetDirty network variable update mechanisms
59 12:10a 🔵 Complete health network variable declarations in player_classified.lua
60 " 🔵 DST classified stat networking follows consistent per-stat event pattern
61 " 🔵 health_replica.lua bridges player_classified net variables to client UI
62 " 🔵 WandaSkill ApplyAgeMax updates component but not player_classified net variable
63 12:11a 🔵 health_replica.lua SetMax() is the correct API for syncing maxhealth to clients
64 12:12a 🔵 Health:SetMaxHealth() exists in server health component at line 503
65 12:13a 🔵 WandaSkill mod already uses SetMaxHealth() but client still doesn't sync
66 12:14a 🔵 Vanilla Wanda uses SetMaxHealth(TUNING.WANDA_OLDAGER=60) successfully
67 " 🔵 Wanda prefab uses health_as_oldage tag and redirect_to_oldager for health management
68 12:15a 🔵 ApplyAgeMax debug logs missing classified.maxhealth:value() line
69 12:16a 🔵 Client log confirms WandaSkill hooks fire but classified not updated client-side
70 12:18a 🔵 Client-side skill hooks fire but ApplyAgeMax never executes on client
71 12:19a 🔵 WandaSkill hooks listen to onactivateskill_server event and defer bonus application
73 " 🔵 SkillTreeData:ActivateSkill validates must_have_one_of/all_of prerequisites before activation
74 " 🔵 ActivateSkill temporarily sets skill, validates, reverts on failure; lock_open can bypass prerequisites
72 " 🔵 OnWandaPostInit gates all event listeners behind ismastersim check — client never runs ApplyAgeMax
75 12:21a 🔵 SkillTreeUpdater has unified ActivateSkill method replacing deprecated Client/Server variants
76 " 🔵 SkillTreeUpdater:ActivateSkill full flow — server pushes onactivateskill_server, client sends RPC
</claude-mem-context>