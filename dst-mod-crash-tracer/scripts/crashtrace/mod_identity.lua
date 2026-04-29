local ModIdentity = {}

local SELF_MOD_HINT = "dst-mod-crash-tracer"

local function normalize_source(source)
    if type(source) ~= "string" then
        return "unknown"
    end

    local normalized = source:gsub("^@", "")
    normalized = normalized:gsub("\\", "/")
    return normalized
end

local function parse_mod_id_from_source(source)
    local normalized = normalize_source(source)
    local mod_id = normalized:match("/mods/([^/]+)/")
    if mod_id ~= nil and mod_id ~= SELF_MOD_HINT then
        return mod_id
    end

    mod_id = normalized:match("^mods/([^/]+)/")
    if mod_id ~= nil and mod_id ~= SELF_MOD_HINT then
        return mod_id
    end

    return nil
end

local function build_unknown(source)
    return {
        mod_id = "unknown",
        mod_name = "unknown",
        source = normalize_source(source),
    }
end

function ModIdentity.FromSource(source)
    local mod_id = parse_mod_id_from_source(source)
    if mod_id == nil then
        return build_unknown(source)
    end

    return {
        mod_id = mod_id,
        mod_name = mod_id,
        source = normalize_source(source),
    }
end

function ModIdentity.CaptureCallerIdentity()
    for level = 3, 10 do
        local info = debug.getinfo(level, "S")
        if info ~= nil then
            local identity = ModIdentity.FromSource(info.source)
            if identity.mod_id ~= "unknown" then
                return identity
            end
        end
    end

    local fallback = debug.getinfo(3, "S")
    return build_unknown(fallback ~= nil and fallback.source or "unknown")
end

return ModIdentity
