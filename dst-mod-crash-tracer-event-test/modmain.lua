local MOD_TAG = "[CrashTraceEventTest]"

print(MOD_TAG .. " modmain loaded")

AddPlayerPostInit(function(inst)
    if inst._crashtrace_event_test_registered then
        return
    end

    inst._crashtrace_event_test_registered = true

    inst:ListenForEvent("crashtrace_test_event", function(player)
        local missing = player.crashtrace_missing_event
        return missing.reason
    end)

    inst:DoTaskInTime(1.3, function(player)
        player:PushEvent("crashtrace_test_event")
    end)
end)
