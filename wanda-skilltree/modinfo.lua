local is_zh = locale == "zh" or locale == "zhr"

name = is_zh and "旺达技能树扩展" or "Wanda Skilltree Expanded"
description = is_zh and [[
为旺达新增技能树：岁月掌控、钟表匠造诣、时空行者、时间支援与亲和栏。

本模组不修改原版代码，所有能力通过 Mod Hook 接入。
]] or [[
Adds a custom skill tree for Wanda.
]]
author = "AI Generated"
version = "0.1.0"

api_version = 10
dst_compatible = true
all_clients_require_mod = true
client_only_mod = false
server_only_mod = false
restart_required = false

server_filter_tags = {
    "wanda",
    "skilltree",
    "pocketwatch",
}

configuration_options = {}
