local MOD_TAG = "[CrashTraceGrassTest]"
local PICKABLE_PREFABS = {
    "grass",
    "sapling",
    "reeds",
    "berrybush",
    "berrybush2",
    "berrybush_juicy",
}

local function register_pick_crash_test(prefab_name)
    AddPrefabPostInit(prefab_name, function(inst)
        if inst._crashtrace_pick_test_registered then
            return
        end

        inst._crashtrace_pick_test_registered = true

        inst:ListenForEvent("picked", function(target, data)
            local picker = data ~= nil and data.picker or nil
            local actual_prefab = target ~= nil and target.prefab or prefab_name

            print(string.format("%s triggering pick crash for prefab=%s", MOD_TAG, tostring(actual_prefab)))

            local missing = picker.crashtrace_missing_pick_target
            return missing.reason
        end)
    end)
end

print(MOD_TAG .. " modmain loaded")

for _, prefab_name in ipairs(PICKABLE_PREFABS) do
    register_pick_crash_test(prefab_name)
end
