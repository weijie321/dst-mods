local ModIdentity = require("crashtrace.mod_identity")
local SafeCall = require("crashtrace.safe_call")
local Logger = require("crashtrace.logger")

local RuntimeHooks = {}

local SELF_MOD_NAME = "dst-mod-crash-tracer"
local unpack_fn = unpack or table.unpack

local function copy_table(source)
    local copy = {}
    if type(source) ~= "table" then
        return copy
    end

    for key, value in pairs(source) do
        copy[key] = value
    end

    return copy
end

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

local function build_event_context(inst, data)
    local context = {}

    if type(inst) == "table" then
        merge_into(context, build_entity_context(inst))
    end

    if type(data) == "table" then
        local picker = data.picker or data.doer or data.attacker or data.owner
        if type(picker) == "table" then
            context.picker = picker.prefab
            context.picker_guid = picker.GUID
        end

        local target = data.target
        if type(target) == "table" and context.target == nil then
            context.target = target.prefab
            context.target_guid = target.GUID
        end
    end

    return context
end

local function should_instrument(identity)
    return type(identity) == "table"
        and identity.mod_id ~= nil
        and identity.mod_id ~= "unknown"
        and identity.mod_id ~= SELF_MOD_NAME
end

local function wrap_runtime_callback(meta, fn, context_builder)
    return function(...)
        local runtime_meta = copy_table(meta)
        merge_into(runtime_meta, context_builder ~= nil and context_builder(...) or nil)
        return SafeCall.Run(runtime_meta, fn, ...)
    end
end

local function mark_wrapped(inst, flag_name)
    if rawget(inst, flag_name) then
        return false
    end

    rawset(inst, flag_name, true)
    return true
end

local function install_listen_for_event_hook(inst)
    if type(inst.ListenForEvent) ~= "function" or not mark_wrapped(inst, "_crashtrace_listen_wrapped") then
        return false
    end

    local original = inst.ListenForEvent
    inst.ListenForEvent = function(self, event, fn, source, ...)
        if type(fn) ~= "function" then
            return original(self, event, fn, source, ...)
        end

        local identity = ModIdentity.CaptureCallerIdentity()
        if not should_instrument(identity) then
            return original(self, event, fn, source, ...)
        end

        local args = { ... }
        args.n = select("#", ...)

        local meta = {
            mod_id = identity.mod_id,
            mod_name = identity.mod_name,
            source = identity.source,
            hook_type = "ListenForEvent",
            action = "event_listener",
            target = event,
            event = event,
        }
        merge_into(meta, build_entity_context(self))

        if type(source) == "table" then
            meta.source_prefab = source.prefab
            meta.source_guid = source.GUID
        end

        local wrapped = wrap_runtime_callback(meta, fn, function(event_inst, data)
            return build_event_context(event_inst, data)
        end)
        return original(self, event, wrapped, source, unpack_fn(args, 1, args.n))
    end

    return true
end

local function install_do_task_in_time_hook(inst)
    if type(inst.DoTaskInTime) ~= "function" or not mark_wrapped(inst, "_crashtrace_task_in_time_wrapped") then
        return false
    end

    local original = inst.DoTaskInTime
    inst.DoTaskInTime = function(self, delay, fn, ...)
        if type(fn) ~= "function" then
            return original(self, delay, fn, ...)
        end

        local identity = ModIdentity.CaptureCallerIdentity()
        if not should_instrument(identity) then
            return original(self, delay, fn, ...)
        end

        local args = { ... }
        args.n = select("#", ...)

        local meta = {
            mod_id = identity.mod_id,
            mod_name = identity.mod_name,
            source = identity.source,
            hook_type = "DoTaskInTime",
            action = "task_in_time",
            target = self.prefab or "unknown",
            delay = delay,
        }
        merge_into(meta, build_entity_context(self))

        local wrapped = wrap_runtime_callback(meta, fn, function(task_inst)
            if type(task_inst) == "table" then
                return build_entity_context(task_inst)
            end
            return {}
        end)

        return original(self, delay, wrapped, unpack_fn(args, 1, args.n))
    end

    return true
end

local function install_do_periodic_task_hook(inst)
    if type(inst.DoPeriodicTask) ~= "function" or not mark_wrapped(inst, "_crashtrace_periodic_task_wrapped") then
        return false
    end

    local original = inst.DoPeriodicTask
    inst.DoPeriodicTask = function(self, interval, fn, initial_delay, ...)
        if type(fn) ~= "function" then
            return original(self, interval, fn, initial_delay, ...)
        end

        local identity = ModIdentity.CaptureCallerIdentity()
        if not should_instrument(identity) then
            return original(self, interval, fn, initial_delay, ...)
        end

        local args = { ... }
        args.n = select("#", ...)

        local meta = {
            mod_id = identity.mod_id,
            mod_name = identity.mod_name,
            source = identity.source,
            hook_type = "DoPeriodicTask",
            action = "periodic_task",
            target = self.prefab or "unknown",
            interval = interval,
            initial_delay = initial_delay,
        }
        merge_into(meta, build_entity_context(self))

        local wrapped = wrap_runtime_callback(meta, fn, function(task_inst)
            if type(task_inst) == "table" then
                return build_entity_context(task_inst)
            end
            return {}
        end)

        return original(self, interval, wrapped, initial_delay, unpack_fn(args, 1, args.n))
    end

    return true
end

function RuntimeHooks.WrapInstance(inst)
    if type(inst) ~= "table" then
        return 0
    end

    if rawget(inst, "_crashtrace_runtime_wrapped") then
        return 0
    end

    rawset(inst, "_crashtrace_runtime_wrapped", true)

    local install_count = 0
    if install_listen_for_event_hook(inst) then
        install_count = install_count + 1
    end
    if install_do_task_in_time_hook(inst) then
        install_count = install_count + 1
    end
    if install_do_periodic_task_hook(inst) then
        install_count = install_count + 1
    end

    return install_count
end

function RuntimeHooks.Install(add_prefab_post_init_any)
    if type(add_prefab_post_init_any) ~= "function" then
        Logger.Info("runtime AddPrefabPostInitAny unavailable")
        return
    end

    add_prefab_post_init_any(function(inst)
        RuntimeHooks.WrapInstance(inst)
    end)

    Logger.Info("runtime hooks registered")
end

return RuntimeHooks
