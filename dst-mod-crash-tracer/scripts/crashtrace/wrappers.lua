local SafeCall = require("crashtrace.safe_call")
local Logger = require("crashtrace.logger")

local Wrappers = {
    _installed = false,
}

local SELF_MOD_NAME = "dst-mod-crash-tracer"
local unpack_fn = unpack or table.unpack

local function merge_into(target, source)
    if type(source) ~= "table" then
        return target
    end

    for key, value in pairs(source) do
        target[key] = value
    end

    return target
end

local function build_entity_context(inst)
    if type(inst) ~= "table" then
        return {}
    end

    return {
        prefab = inst.prefab,
        guid = inst.GUID,
    }
end

local function wrap_callback(meta, fn, context_builder)
    return function(...)
        local runtime_meta = {}
        merge_into(runtime_meta, meta)
        merge_into(runtime_meta, context_builder ~= nil and context_builder(...) or nil)
        return SafeCall.Run(runtime_meta, fn, ...)
    end
end

local function build_env_identity(env)
    local mod_name = env.modname or "unknown"
    local mod_fancy_name = mod_name

    if type(env.modinfo) == "table" and type(env.modinfo.name) == "string" and env.modinfo.name ~= "" then
        mod_fancy_name = env.modinfo.name
    end

    return {
        mod_id = mod_name,
        mod_name = mod_fancy_name,
        source = (env.MODROOT or ("../mods/" .. mod_name .. "/")) .. "modmain.lua",
    }
end

local function wrap_env_api(env, field_name, hook_type, action, build_meta, context_builder)
    local original = rawget(env, field_name)
    if type(original) ~= "function" then
        return false
    end

    rawset(env, field_name, function(...)
        local args = { ... }
        local callback = args[#args]
        if type(callback) ~= "function" then
            return original(unpack_fn(args, 1, #args))
        end

        if field_name == "AddPrefabPostInitAny" and rawget(env, "_crashtrace_registering_player_post_init") then
            return original(unpack_fn(args, 1, #args))
        end

        local identity = build_env_identity(env)
        local meta = {
            mod_id = identity.mod_id,
            mod_name = identity.mod_name,
            source = identity.source,
            hook_type = hook_type,
            action = action,
        }
        merge_into(meta, build_meta ~= nil and build_meta(args) or nil)

        if field_name == "AddPlayerPostInit" then
            rawset(env, "_crashtrace_registering_player_post_init", true)
        end
        args[#args] = wrap_callback(meta, callback, context_builder)
        local results = { original(unpack_fn(args, 1, #args)) }
        if field_name == "AddPlayerPostInit" then
            rawset(env, "_crashtrace_registering_player_post_init", nil)
        end
        return unpack_fn(results, 1, #results)
    end)

    return true
end

local function install_wrappers_for_env(env)
    if type(env) ~= "table" or env.modname == nil then
        return 0
    end

    if env.modname == SELF_MOD_NAME then
        return 0
    end

    if rawget(env, "_crashtrace_wrapped") then
        return 0
    end

    local install_count = 0

    if wrap_env_api(
        env,
        "AddPrefabPostInit",
        "AddPrefabPostInit",
        "prefab_post_init",
        function(args)
            return { target = args[1] }
        end,
        function(inst)
            return build_entity_context(inst)
        end
    ) then
        install_count = install_count + 1
    end

    if wrap_env_api(
        env,
        "AddPrefabPostInitAny",
        "AddPrefabPostInitAny",
        "prefab_post_init_any",
        function()
            return { target = "any_prefab" }
        end,
        function(inst)
            local entity_context = build_entity_context(inst)
            if entity_context.prefab ~= nil then
                entity_context.target = entity_context.prefab
            end
            return entity_context
        end
    ) then
        install_count = install_count + 1
    end

    if wrap_env_api(
        env,
        "AddPlayerPostInit",
        "AddPlayerPostInit",
        "player_post_init",
        function()
            return { target = "player" }
        end,
        function(inst)
            return build_entity_context(inst)
        end
    ) then
        install_count = install_count + 1
    end

    if wrap_env_api(
        env,
        "AddComponentPostInit",
        "AddComponentPostInit",
        "component_post_init",
        function(args)
            return { target = args[1], component = args[1] }
        end,
        function(component)
            if type(component) ~= "table" then
                return {}
            end

            return build_entity_context(component.inst)
        end
    ) then
        install_count = install_count + 1
    end

    if wrap_env_api(
        env,
        "AddGamePostInit",
        "AddGamePostInit",
        "game_post_init",
        function()
            return { target = "game" }
        end,
        nil
    ) then
        install_count = install_count + 1
    end

    if wrap_env_api(
        env,
        "AddSimPostInit",
        "AddSimPostInit",
        "sim_post_init",
        function()
            return { target = "sim" }
        end,
        function(inst)
            return build_entity_context(inst)
        end
    ) then
        install_count = install_count + 1
    end

    rawset(env, "_crashtrace_wrapped", true)
    return install_count
end

local function install_wrappers_for_loaded_mods()
    local mod_manager = rawget(_G, "ModManager")
    if type(mod_manager) ~= "table" or type(mod_manager.mods) ~= "table" then
        Logger.Info("ModManager unavailable")
        return
    end

    local wrapped_mods = 0
    local wrapped_apis = 0

    for _, mod_env in ipairs(mod_manager.mods) do
        local installed = install_wrappers_for_env(mod_env)
        if installed > 0 then
            wrapped_mods = wrapped_mods + 1
            wrapped_apis = wrapped_apis + installed
        end
    end

    Logger.Info(string.format("wrapped %d apis across %d mods", wrapped_apis, wrapped_mods))
end

function Wrappers.Install()
    if Wrappers._installed then
        Logger.Info("wrappers already installed")
        return
    end

    install_wrappers_for_loaded_mods()

    Wrappers._installed = true
    Logger.Info("env wrappers installed")
end

return Wrappers
