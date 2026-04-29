local Context = require("crashtrace.context")
local Logger = require("crashtrace.logger")

local SafeCall = {}

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

local function pack_results(...)
    return {
        n = select("#", ...),
        ...
    }
end

local function build_report(meta, error_payload)
    local report = copy_table(meta)

    if type(error_payload) == "table" then
        report.error = error_payload.message or "unknown error"
        report.traceback = error_payload.traceback or tostring(error_payload.message or "unknown error")
    else
        report.error = tostring(error_payload)
        report.traceback = tostring(error_payload)
    end

    return report
end

local function should_skip_nested_report(meta)
    if type(meta) ~= "table" then
        return false
    end

    if meta.action == "prefab_post_init_any" and Context.HasParentAction("player_post_init") then
        return true
    end

    return false
end

function SafeCall.Run(meta, fn, ...)
    if type(fn) ~= "function" then
        return false, "target is not callable"
    end

    local args = { ... }
    args.n = select("#", ...)
    local runtime_meta = copy_table(meta)

    Context.Push(runtime_meta)

    local function error_handler(err)
        local prefix = "[CrashTrace]"
        local action = runtime_meta.action or "unknown_action"
        local message = tostring(err)
        return {
            message = message,
            traceback = debug.traceback(string.format("%s %s: %s", prefix, action, message), 2),
        }
    end

    local function invoke()
        return fn(unpack_fn(args, 1, args.n))
    end

    local results = pack_results(xpcall(invoke, error_handler))
    Context.Pop()

    local ok = results[1]
    if not ok then
        if not should_skip_nested_report(runtime_meta) then
            Logger.Report(build_report(runtime_meta, results[2]))
        end
        return nil
    end

    return unpack_fn(results, 2, results.n)
end

return SafeCall
