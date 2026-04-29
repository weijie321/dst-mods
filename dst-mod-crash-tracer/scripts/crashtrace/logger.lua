local Config = require("crashtrace.config")
local ReportBuilder = require("crashtrace.report_builder")

local Logger = {}

local function format_line(level, message)
    return string.format("[CrashTrace][%s] %s", level, tostring(message))
end

local function print_lines(level, lines)
    for _, line in ipairs(lines) do
        print(format_line(level, line))
    end
end

function Logger.Info(message)
    print(format_line("INFO", message))
end

function Logger.Error(message)
    print(format_line("ERROR", message))
end

function Logger.Report(report)
    if type(report) ~= "table" then
        Logger.Error("invalid report payload")
        return
    end

    Logger.Error("report_begin")
    Logger.Error(Config.GetText("report_intro"))
    print_lines("ERROR", ReportBuilder.BuildSummaryLines(report))
    Logger.Error("tip=" .. Config.GetText("report_tip"))
    Logger.Error("traceback_begin")
    print_lines("TRACE", ReportBuilder.BuildTracebackLines(report))
    Logger.Error("traceback_end")
    Logger.Error("report_end")
end

return Logger
