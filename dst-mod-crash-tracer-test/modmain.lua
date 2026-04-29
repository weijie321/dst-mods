local MOD_TAG = "[CrashTraceTest]"

print(MOD_TAG .. " modmain loaded")

AddPlayerPostInit(function(inst)
    if inst._crashtrace_postinit_test_registered then
        return
    end

    inst._crashtrace_postinit_test_registered = true

    inst:DoTaskInTime(0.9, function(player)
        local missing = player.not_exists
        return missing.prefab
    end)
end)
