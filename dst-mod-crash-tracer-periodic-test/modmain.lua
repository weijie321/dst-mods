local MOD_TAG = "[CrashTracePeriodicTest]"

print(MOD_TAG .. " modmain loaded")

AddPlayerPostInit(function(inst)
    if inst._crashtrace_periodic_test_registered then
        return
    end

    inst._crashtrace_periodic_test_registered = true

    local task = nil
    task = inst:DoPeriodicTask(0.3, function(player)
        if task ~= nil then
            task:Cancel()
        end

        local missing = player.crashtrace_missing_periodic
        return missing.reason
    end, 0.5)
end)
