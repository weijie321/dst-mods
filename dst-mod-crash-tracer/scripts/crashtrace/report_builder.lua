local Config = require("crashtrace.config")
local I18N = require("crashtrace.i18n")

local ReportBuilder = {}

local function safe_value(value, default)
    if value == nil or value == "" then
        return default or "unknown"
    end

    return tostring(value)
end

local function split_lines(text)
    local lines = {}
    local value = tostring(text or "")

    for line in value:gmatch("([^\r\n]+)") do
        lines[#lines + 1] = line
    end

    if #lines == 0 then
        lines[1] = value
    end

    return lines
end

function ReportBuilder.BuildSummaryLines(report)
    local lines = {
        "title=" .. Config.GetText("report_title"),
        "language=" .. Config.GetLanguage(),
        "version=" .. Config.GetVersion(),
        "mod_id=" .. safe_value(report.mod_id),
        "mod_name=" .. safe_value(report.mod_name),
        "hook_type=" .. safe_value(report.hook_type),
        "hook_label=" .. safe_value(I18N.LocalizeHook(report.hook_type)),
        "action=" .. safe_value(report.action),
        "action_label=" .. safe_value(I18N.LocalizeAction(report.action)),
        "event=" .. safe_value(report.event),
        "event_label=" .. safe_value(I18N.LocalizeEvent(report.event)),
        "picker=" .. safe_value(report.picker or report.player),
        "picker_label=" .. safe_value(I18N.LocalizePrefab(report.picker or report.player)),
        "target=" .. safe_value(report.target),
        "target_label=" .. safe_value(I18N.LocalizePrefab(report.target)),
        "prefab=" .. safe_value(report.prefab),
        "prefab_label=" .. safe_value(I18N.LocalizePrefab(report.prefab)),
        "guid=" .. safe_value(report.guid),
        "trigger_summary=" .. safe_value(I18N.BuildTriggerSummary(report)),
        "reason=" .. safe_value(report.error),
        "source=" .. safe_value(report.source),
    }

    return lines
end

function ReportBuilder.BuildTracebackLines(report)
    return split_lines(report.traceback or "")
end

return ReportBuilder
