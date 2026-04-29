local Config = {
    language = "zh",
    version = "0.2.0",
}

local TEXTS = {
    zh = {
        report_title = "检测到 mod 异常",
        report_intro = "捕获到 Lua mod 异常",
        report_tip = "可运行 E:\\work\\code\\ai-generated\\dst-mods\\查看最新CrashTrace报告.bat 查看最近一次摘要",
        bootstrap_start = "bootstrap start",
        bootstrap_ready = "phase 1 runtime initialized",
    },
    en = {
        report_title = "Mod exception detected",
        report_intro = "Lua mod exception captured",
        report_tip = "Run E:\\work\\code\\ai-generated\\dst-mods\\view_latest_crashtrace_report.bat to view the latest summary",
        bootstrap_start = "bootstrap start",
        bootstrap_ready = "phase 1 runtime initialized",
    },
}

local function normalize_language(value)
    if value == "en" then
        return "en"
    end

    return "zh"
end

function Config.SetLanguage(value)
    Config.language = normalize_language(value)
end

function Config.GetLanguage()
    return Config.language
end

function Config.GetVersion()
    return Config.version
end

function Config.GetText(key)
    local lang = Config.GetLanguage()
    local text_group = TEXTS[lang] or TEXTS.zh
    return text_group[key] or TEXTS.zh[key] or key
end

return Config
