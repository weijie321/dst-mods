modimport("probe_config.lua")
local G = GLOBAL
local token = PROBE_RUN_ID
local character = PROBE_CHARACTER
local namespace = "dstwf_client_" .. token
local json = G.require("json")
local failed, completed, started = false, false, false
local pending, done_requested, done_detail = 0, false, nil

local function emit(data)
    data.side = "client"
    G.print("[DST_CLIENT:" .. token .. "] " .. json.encode(data))
end

local function finish(ok, detail)
    SendModRPCToServer(GetModRPC(namespace, "finish"), token, ok, G.tostring(detail or ""))
end

local test = {}
function test.Fail(reason)
    failed = true
    emit({ event = "fail", details = G.tostring(reason) })
    finish(false, reason)
end
function test.Blocked(reason)
    failed = true
    emit({event="blocked", details=G.tostring(reason)})
    finish(false, reason)
end
function test.Assert(name, ok, details)
    emit({ event = "assert", name = name, ok = ok == true, details = details })
    if ok ~= true then
        failed = true
        finish(false, name)
    end
    return ok == true
end
local function complete_if_ready()
    if failed or completed or not done_requested or pending > 0 then return end
    completed = true
    emit({ event = "done", details = done_detail or "客户端断言完成" })
    finish(true, done_detail)
end
function test.Done(detail)
    done_requested, done_detail = true, detail
    complete_if_ready()
end
function test.After(seconds, callback)
    if completed then test.Fail("Done 后不能新增异步断言") return end
    pending = pending + 1
    return G.TheWorld:DoTaskInTime(seconds, function()
        local ok, err = G.xpcall(callback, G.debug.traceback)
        pending = pending - 1
        if not ok then test.Fail(err) end
        complete_if_ready()
    end)
end
test.assert, test.emit = test.Assert, emit
test.target_character = character

AddModRPCHandler(namespace, "finish", function(player, run_id, ok, detail)
    if run_id ~= token or player == nil or not player:IsValid() or G.type(ok) ~= "boolean" then return end
    G.TheWorld:PushEvent("dstwf_client_done", {run_id=token, ok=ok, details=detail, player=player})
end)

AddModRPCHandler(namespace, "challenge", function(player, run_id)
    if run_id ~= token or player == nil or not player:IsValid() then return end
    local health = player.components.health
    SendModRPCToClient(GetClientModRPC(namespace, "response"), player.userid, token,
        player.prefab, health ~= nil and health.maxhealth or -1)
end)

local function custom_tests()
    if not PROBE_HAS_SCRIPT then
        test.Done("连接、HUD、health Replica 基础验证；未提供专项行为断言")
        return
    end
    local fn = G.kleiloadlua(MODROOT .. "client_test.lua")
    if G.type(fn) ~= "function" then test.Fail("客户端断言脚本加载失败：" .. G.tostring(fn)) return end
    G.setfenv(fn, G.setmetatable({GLOBAL=G, TEST=test}, {__index=G}))
    local ok, result = G.xpcall(fn, G.debug.traceback)
    if not ok then test.Fail(result) return end
    if G.type(result) == "function" then
        ok, result = G.xpcall(function() result(test) end, G.debug.traceback)
        if not ok then test.Fail(result) end
    end
    -- 返回不代表异步断言完成；专项脚本必须显式调用 TEST.Done()。
end

AddClientModRPCHandler(namespace, "response", function(run_id, prefab, maxhealth)
    if run_id ~= token or started then return end
    started = true
    local player = G.ThePlayer
    local health = player ~= nil and player.replica.health or nil
    test.Assert("client_server_identity", prefab == character and player ~= nil and player.prefab == character, prefab)
    test.Assert("client_health_replica_present", health ~= nil and health.classified ~= nil)
    test.Assert("client_health_max_matches_server", health ~= nil and health:Max() == maxhealth,
        {server=maxhealth, client=health ~= nil and health:Max() or -1})
    emit({event="replica", prefab=prefab, server_maxhealth=maxhealth,
        client_maxhealth=health ~= nil and health:Max() or -1})
    if not failed then custom_tests() end
end)

if not G.TheNet:IsDedicated() then
    emit({event="ready"})
    AddClassPostConstruct("screens/redux/lobbyscreen", function(screen)
        screen.inst:DoTaskInTime(1, function()
            local ok, err = G.xpcall(function()
                if screen.cb == nil then test.Fail("选角回调不可用") return end
                if G.TheInventory:HasSupportForOfflineSkins() and not G.TheInventory:HasDownloadedInventory() then
                    G.TheInventory:ForceLoadOfflineCache()
                end
                emit({event="character_ownership", prefab=character, owned=G.IsCharacterOwned(character)})
                if not G.IsCharacterOwned(character) then test.Blocked("官方库存校验未确认当前账号拥有角色：" .. character) return end
                screen.cb(character, character .. "_none", "", "", "", "")
            end, G.debug.traceback)
            if not ok then test.Fail(err) end
        end)
    end)
    AddPrefabPostInit("world", function(world)
        if world.ismastersim then test.Fail("目标必须是独立远端客户端") return end
        local ticks, requested = 0, false
        local task
        task = world:DoPeriodicTask(0.5, function()
            local ok, err = G.xpcall(function()
                ticks = ticks + 1
                local player = G.ThePlayer
                local hud = player ~= nil and player.HUD or nil
                local controls = hud ~= nil and hud.controls or nil
                local status = controls ~= nil and controls.status or nil
                local health = player ~= nil and player.replica.health or nil
                if not requested and player ~= nil and status ~= nil and status.heart ~= nil and health ~= nil and health.classified ~= nil then
                    requested = true
                    emit({event="player", prefab=player.prefab})
                    emit({event="hud", controls=true, health_badge=true})
                    test.Assert("client_is_remote", not world.ismastersim and not G.TheNet:GetIsServer())
                    test.Assert("client_hud_ready", status.heart ~= nil)
                    SendModRPCToServer(GetModRPC(namespace, "challenge"), token)
                end
                if completed or failed or ticks >= 180 then
                    task:Cancel()
                    if not completed and not failed then test.Fail("未取得玩家、HUD 或服务器响应") end
                end
            end, G.debug.traceback)
            if not ok then task:Cancel() test.Fail(err) end
        end)
    end)
end
