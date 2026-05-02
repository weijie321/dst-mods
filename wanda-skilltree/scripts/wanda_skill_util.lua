local WandaSkillUtil = {}

local function GetSkillTree(inst)
    return inst ~= nil and inst.components ~= nil and inst.components.skilltreeupdater or nil
end

function WandaSkillUtil.HasSkill(inst, skill)
    local updater = GetSkillTree(inst)
    return updater ~= nil and updater:IsActivated(skill)
end

function WandaSkillUtil.HasAnySkill(inst, skills)
    for _, skill in ipairs(skills) do
        if WandaSkillUtil.HasSkill(inst, skill) then
            return true
        end
    end
    return false
end

function WandaSkillUtil.GetAgeMax(inst)
    if WandaSkillUtil.HasSkill(inst, "wanda_age_max_3") then
        return 150
    elseif WandaSkillUtil.HasSkill(inst, "wanda_age_max_2") then
        return 120
    elseif WandaSkillUtil.HasSkill(inst, "wanda_age_max_1") then
        return 100
    end
    return TUNING.WANDA_OLDAGER
end

function WandaSkillUtil.GetHealBonus(inst)
    if WandaSkillUtil.HasSkill(inst, "wanda_heal_bonus_3") then
        return 10
    elseif WandaSkillUtil.HasSkill(inst, "wanda_heal_bonus_2") then
        return 5
    elseif WandaSkillUtil.HasSkill(inst, "wanda_heal_bonus_1") then
        return 2
    end
    return 0
end

function WandaSkillUtil.IsWanda(inst)
    return inst ~= nil and inst.prefab == "wanda"
end

function WandaSkillUtil.IsAlarmWeapon(inst)
    return inst ~= nil and (inst.prefab == "pocketwatch_weapon" or inst:HasTag("wanda_alarm_weapon"))
end

function WandaSkillUtil.GetGrandOwner(inst)
    return inst ~= nil
        and inst.components ~= nil
        and inst.components.inventoryitem ~= nil
        and inst.components.inventoryitem:GetGrandOwner()
        or nil
end

function WandaSkillUtil.FindNearbyTeammates(inst, radius)
    local result = {}
    if inst == nil or inst.Transform == nil then
        return result
    end

    local x, y, z = inst.Transform:GetWorldPosition()
    for _, player in ipairs(AllPlayers) do
        if player ~= inst
            and player:IsValid()
            and not player:HasTag("playerghost")
            and player.components ~= nil
            and player.components.health ~= nil
            and not player.components.health:IsDead()
            and player:GetDistanceSqToPoint(x, y, z) <= radius * radius
        then
            table.insert(result, player)
        end
    end
    return result
end

function WandaSkillUtil.ProtectForFrames(player, frames)
    if player == nil or player.components == nil or player.components.health == nil then
        return
    end
    player.components.health:SetInvincible(true)
    player:DoTaskInTime((frames or 1) * FRAMES, function()
        if player:IsValid() and player.components.health ~= nil then
            player.components.health:SetInvincible(false)
        end
    end)
end

function WandaSkillUtil.FindPlayerByUserid(userid)
    if userid == nil then
        return nil
    end
    for _, player in ipairs(AllPlayers) do
        if player.userid == userid then
            return player
        end
    end
    return nil
end

local function ScanContainer(container, predicate)
    if container == nil then
        return nil
    end
    for _, item in pairs(container.slots or {}) do
        if predicate(item) then
            return item
        end
        if item.components ~= nil and item.components.container ~= nil then
            local found = ScanContainer(item.components.container, predicate)
            if found ~= nil then
                return found
            end
        end
    end
    return nil
end

function WandaSkillUtil.FindBondedRecallWatch(owner, userid)
    if owner == nil or owner.components == nil or owner.components.inventory == nil then
        return nil
    end
    local function predicate(item)
        return item ~= nil
            and item.prefab == "pocketwatch_recall"
            and item.wanda_bond_userid == userid
    end

    local inventory = owner.components.inventory
    for _, item in pairs(inventory.itemslots or {}) do
        if predicate(item) then
            return item
        end
        if item.components ~= nil and item.components.container ~= nil then
            local found = ScanContainer(item.components.container, predicate)
            if found ~= nil then
                return found
            end
        end
    end

    for _, item in pairs(inventory.equipslots or {}) do
        if predicate(item) then
            return item
        end
        if item.components ~= nil and item.components.container ~= nil then
            local found = ScanContainer(item.components.container, predicate)
            if found ~= nil then
                return found
            end
        end
    end
end

return WandaSkillUtil
