local Config = require("crashtrace.config")
local Logger = require("crashtrace.logger")
local RuntimeHooks = require("crashtrace.runtime_hooks")

local function bootstrap()
    if type(GetModConfigData) == "function" then
        Config.SetLanguage(GetModConfigData("language", true))
    end

    Logger.Info(string.format("%s v%s lang=%s", Config.GetText("bootstrap_start"), Config.GetVersion(), Config.GetLanguage()))
    if type(AddPrefabPostInitAny) == "function" then
        RuntimeHooks.Install(AddPrefabPostInitAny)
    else
        Logger.Info("AddPrefabPostInitAny unavailable for runtime hooks")
    end
    Logger.Info(Config.GetText("bootstrap_ready"))
end

bootstrap()
