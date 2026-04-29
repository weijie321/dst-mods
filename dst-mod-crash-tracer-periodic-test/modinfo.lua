name = "Crash Tracer Periodic Test / 周期任务异常测试"
description = [[Intentional periodic task failure for validating CrashTrace runtime task hooks.
Best used when verifying DoPeriodicTask capture.
Version: 0.2.0

用于验证 CrashTrace 运行期周期任务 Hook 的测试 mod。
主要用于验证 DoPeriodicTask 异常捕获。
版本: 0.2.0]]
author = "Cursor + User"
version = "0.2.0"

forumthread = ""

api_version = 10

dst_compatible = true
client_only_mod = false
all_clients_require_mod = false

server_filter_tags = {
    "debug",
    "diagnostic",
    "crashtrace-periodic-test",
}

icon_atlas = nil
icon = nil
