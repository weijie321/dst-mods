local MOD_TAG = "[CrashTraceTaskTest]"

print(MOD_TAG .. " modmain loaded")

AddPlayerPostInit(function(inst)
    if inst._crashtrace_task_test_registered then
        return
    end

    inst._crashtrace_task_test_registered = true

    inst:DoTaskInTime(0.2, function(player)
        local missing = player.crashtrace_missing_task
        return missing.reason
    end)
end)
