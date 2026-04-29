name = "DST Mod Crash Tracer / 饥荒 Mod 异常追踪"
description = [[Capture and attribute Lua-layer mod exceptions for diagnostics.
Supports structured crash reports for player post init, event listeners, delayed tasks, and periodic tasks.
Version: 0.2.0

用于捕获并归因 Lua 层 mod 异常的诊断工具。
当前支持玩家初始化、事件监听、延时任务、周期任务的结构化异常报告。
版本: 0.2.0]]
author = "Cursor + User"
version = "0.2.0"
priority = 1000000

forumthread = ""

api_version = 10

dst_compatible = true
client_only_mod = false
all_clients_require_mod = false

server_filter_tags = {
    "debug",
    "diagnostic",
    "crashtrace",
}

configuration_options = {
    {
        name = "language",
        label = "Language / 语言",
        hover = "Switch CrashTrace in-game report language between Chinese and English. / 切换 CrashTrace 在游戏内输出的中英文。",
        options = {
            { description = "中文", data = "zh" },
            { description = "English", data = "en" },
        },
        default = "zh",
    },
}

icon_atlas = nil
icon = nil
