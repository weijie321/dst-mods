local util = require("wanda_skill_util")
local writeables = require("writeables")

local TIMEBOX_SLOT = TUNING.WANDA_SKILLTREE_MOD.TIMEBOX_SLOT
EQUIPSLOTS.WANDA_TIMEBOX = TIMEBOX_SLOT

local OLD_CALM_SOURCE = "wanda_old_calm"
local OLD_CALM_WORK_MULT = TUNING.MIGHTY_WORK_EFFECTIVENESS or 1.5

local function IsWandaOld(inst)
    return inst ~= nil and inst.age_state == "old"
end

if writeables.GetLayout("pocketwatch_recall") == nil then
    writeables.AddLayout("pocketwatch_recall", {
        prompt = STRINGS.WANDA_RENAME_WATCH.PROMPT,
        animbank = "ui_board_5x3",
        animbuild = "ui_board_5x3",
        menuoffset = Vector3(6, -70, 0),
        maxcharacters = 30,
        defaulttext = function(inst)
            return inst.components.writeable ~= nil and inst.components.writeable:GetText() or ""
        end,
        cancelbtn = { text = STRINGS.SIGNS.MENU.CANCEL, cb = nil, control = CONTROL_CANCEL },
        acceptbtn = { text = STRINGS.SIGNS.MENU.ACCEPT, cb = nil, control = CONTROL_ACCEPT },
    })
end
if writeables.GetLayout("pocketwatch_portal") == nil then
    writeables.AddLayout("pocketwatch_portal", writeables.GetLayout("pocketwatch_recall"))
end

local function RemoveOldCalmBonuses(inst)
    inst:RemoveTag("wanda_old_calm")
    inst:RemoveTag("mightiness_mighty")

    if inst.components.workmultiplier ~= nil then
        inst.components.workmultiplier:RemoveMultiplier(ACTIONS.CHOP, OLD_CALM_SOURCE)
        inst.components.workmultiplier:RemoveMultiplier(ACTIONS.MINE, OLD_CALM_SOURCE)
        inst.components.workmultiplier:RemoveMultiplier(ACTIONS.HAMMER, OLD_CALM_SOURCE)
    end
    if inst.components.efficientuser ~= nil then
        inst.components.efficientuser:RemoveMultiplier(ACTIONS.CHOP, OLD_CALM_SOURCE)
        inst.components.efficientuser:RemoveMultiplier(ACTIONS.MINE, OLD_CALM_SOURCE)
        inst.components.efficientuser:RemoveMultiplier(ACTIONS.HAMMER, OLD_CALM_SOURCE)
    end
    if inst.components.expertsailor ~= nil then
        inst.components.expertsailor:SetRowForceMultiplier(nil)
        inst.components.expertsailor:SetRowExtraMaxVelocity(nil)
        inst.components.expertsailor:SetAnchorRaisingSpeed(nil)
        inst.components.expertsailor:SetLowerSailStrength(nil)
    end

    if IsWandaOld(inst) then
        inst:AddTag("slowbuilder")
        if inst.components.inventory ~= nil then
            inst.components.inventory.noheavylifting = true
        end
        if inst.components.workmultiplier ~= nil then
            inst.components.workmultiplier:AddMultiplier(ACTIONS.HAMMER, TUNING.WANDA_OLD_HAMMER_EFFECTIVENESS, inst)
        end
    end
end

local function ApplyOldCalm(inst)
    if not IsWandaOld(inst) then
        RemoveOldCalmBonuses(inst)
        return
    end

    if util.HasSkill(inst, "wanda_old_calm") then
        inst:AddTag("wanda_old_calm")
        inst:AddTag("mightiness_mighty")
        inst:RemoveTag("slowbuilder")
        if inst.components.inventory ~= nil then
            inst.components.inventory.noheavylifting = false
        end
        if inst.components.efficientuser == nil then
            inst:AddComponent("efficientuser")
        end
        if inst.components.expertsailor == nil then
            inst:AddComponent("expertsailor")
        end
        if inst.components.workmultiplier ~= nil then
            inst.components.workmultiplier:RemoveMultiplier(ACTIONS.HAMMER, inst)
            inst.components.workmultiplier:AddMultiplier(ACTIONS.CHOP, OLD_CALM_WORK_MULT, OLD_CALM_SOURCE)
            inst.components.workmultiplier:AddMultiplier(ACTIONS.MINE, OLD_CALM_WORK_MULT, OLD_CALM_SOURCE)
            inst.components.workmultiplier:AddMultiplier(ACTIONS.HAMMER, OLD_CALM_WORK_MULT, OLD_CALM_SOURCE)
        end
        if inst.components.efficientuser ~= nil then
            inst.components.efficientuser:AddMultiplier(ACTIONS.CHOP, OLD_CALM_WORK_MULT, OLD_CALM_SOURCE)
            inst.components.efficientuser:AddMultiplier(ACTIONS.MINE, OLD_CALM_WORK_MULT, OLD_CALM_SOURCE)
            inst.components.efficientuser:AddMultiplier(ACTIONS.HAMMER, OLD_CALM_WORK_MULT, OLD_CALM_SOURCE)
        end
        if inst.components.expertsailor ~= nil then
            inst.components.expertsailor:SetRowForceMultiplier(TUNING.MIGHTY_ROWER_MULT)
            inst.components.expertsailor:SetRowExtraMaxVelocity(TUNING.MIGHTY_ROWER_EXTRA_MAX_VELOCITY)
            inst.components.expertsailor:SetAnchorRaisingSpeed(TUNING.MIGHTY_ANCHOR_SPEED)
            inst.components.expertsailor:SetLowerSailStrength(TUNING.MIGHTY_SAIL_BOOST_STRENGTH)
        end
    else
        RemoveOldCalmBonuses(inst)
    end
end

local function ApplyPlanarDefense(inst)
    if inst.components.planardefense == nil then
        inst:AddComponent("planardefense")
    end

    if inst.components.planardefense ~= nil then
        if util.HasSkill(inst, "wanda_planar_defense") then
            inst.components.planardefense:SetBaseDefense(0.5)
        else
            inst.components.planardefense:SetBaseDefense(0)
        end
    end
end

local function ForceHealthHUDUpdate(inst)
    if inst.components == nil or inst.components.health == nil then
        return
    end

    if inst.components.oldager ~= nil then
        inst.components.oldager._taking_time_damage = true
        inst.components.health:ForceUpdateHUD(true)
        inst.components.oldager._taking_time_damage = false
    else
        inst.components.health:ForceUpdateHUD(true)
    end
end

local function ApplyAgeMax(inst)
    if inst.components == nil or inst.components.health == nil then
        return
    end

    local health = inst.components.health
    local current_display_max = TUNING.WANDA_MIN_YEARS_OLD + health.maxhealth
    local current_age = current_display_max - health.currenthealth
    local new_display_max = util.GetAgeDisplayMax(inst)
    local new_health_max = util.GetAgeHealthMax(inst)

    local new_current = math.clamp(new_display_max - current_age, 0, new_health_max)
    if not health:IsDead() and new_current <= 0 then
        new_current = 1
    end

    if health.maxhealth ~= new_health_max or health.currenthealth ~= new_current then
        health:SetMaxHealth(new_health_max)
        health:SetCurrentHealth(new_current)
        ForceHealthHUDUpdate(inst)
    end
end

local function ApplyRecipeTags(inst)
    for _, tag in ipairs({
        "wanda_timebox_1",
        "wanda_timebox_2",
        "wanda_timebox_3",
        "wanda_desperate_alarm",
    }) do
        if util.HasSkill(inst, tag) then
            inst:AddTag(tag)
        else
            inst:RemoveTag(tag)
        end
    end
end

local function ApplyWandaSkillTreeBonuses(inst)
    ApplyAgeMax(inst)
    ApplyOldCalm(inst)
    ApplyPlanarDefense(inst)
    ApplyRecipeTags(inst)
end

local function OnWandaSkillChanged(inst)
    inst:DoTaskInTime(0, ApplyWandaSkillTreeBonuses)
end

local function OnWandaPostInit(inst)
    inst.ApplyWandaSkillTreeBonuses = ApplyWandaSkillTreeBonuses

    if not TheWorld.ismastersim then
        return
    end

    if inst.components.oldager ~= nil then
        inst.components.oldager:AddValidHealingCause("wanda_heal_bonus")
    end

    inst:ListenForEvent("ms_skilltreeinitialized", OnWandaSkillChanged)
    inst:ListenForEvent("onactivateskill_server", OnWandaSkillChanged)
    inst:ListenForEvent("ondeactivateskill_server", OnWandaSkillChanged)
    inst:ListenForEvent("healthdelta", function()
        ApplyOldCalm(inst)
    end)
    inst:ListenForEvent("onwarpback", function(inst)
        if util.HasSkill(inst, "wanda_warp_speed") and inst.components.locomotor ~= nil then
            inst.components.locomotor:SetExternalSpeedMultiplier(inst, "wanda_warp_speed", TUNING.WANDA_SKILLTREE_MOD.WARP_SPEED_MULT)
            inst:DoTaskInTime(TUNING.WANDA_SKILLTREE_MOD.WARP_SPEED_TIME, function()
                if inst:IsValid() and inst.components.locomotor ~= nil then
                    inst.components.locomotor:RemoveExternalSpeedMultiplier(inst, "wanda_warp_speed")
                end
            end)
        end

        if util.HasSkill(inst, "wanda_warp_shadow") and inst.wanda_last_warp_origin ~= nil then
            local decoy = SpawnPrefab("wanda_time_decoy")
            if decoy ~= nil then
                decoy.Transform:SetPosition(inst.wanda_last_warp_origin:Get())
            end
        end
        inst.wanda_last_warp_origin = nil
    end)

    inst:DoTaskInTime(0, ApplyWandaSkillTreeBonuses)
end

AddPrefabPostInit("wanda", OnWandaPostInit)

AddPrefabPostInit("wanda", function(inst)
    local old_speed_modifier = inst.inventory_EquippableWalkSpeedMultModifier
    inst.inventory_EquippableWalkSpeedMultModifier = function(owner, speed, item)
        if owner ~= nil and owner:HasTag("wanda_old_calm") and speed < 1 then
            return 1
        end
        return old_speed_modifier ~= nil and old_speed_modifier(owner, speed, item) or speed
    end
end)

local function RefreshExternalWandaAgeBadgeMax(self)
    if self.wanda_current_age == nil or self.wanda_max_age == nil then
        return
    end

    self.num:SetString(tostring(self.wanda_current_age))

    if self.CombinedStatusUpdateNumbers ~= nil then
        local old_is_wanda_oldage_badge = self._iswandaoldagebadge
        self._iswandaoldagebadge = false
        self:CombinedStatusUpdateNumbers(self.wanda_max_age)
        self._iswandaoldagebadge = old_is_wanda_oldage_badge
    end
end

AddClassPostConstruct("widgets/wandaagebadge", function(self)
    local old_SetPercent = self.SetPercent

    self.SetPercent = function(self, val, max, penaltypercent)
        if old_SetPercent ~= nil then
            old_SetPercent(self, val, max, penaltypercent)
        end

        local display_max_age = TUNING.WANDA_MIN_YEARS_OLD + (max or TUNING.WANDA_OLDAGER)
        local age_percent = 1 - val
        local age = TUNING.WANDA_MIN_YEARS_OLD + age_percent * (display_max_age - TUNING.WANDA_MIN_YEARS_OLD)

        self.health_precent = val
        self.percent = val
        self.wanda_current_age = math.floor(age + 0.5)
        self.wanda_max_age = math.floor(display_max_age + 0.5)

        RefreshExternalWandaAgeBadgeMax(self)
        self.year_hand:SetRotation(Lerp(0, 360, age_percent))
    end
end)

-- Ensure wanda's skillxp is initialized so ActivateSkill validation passes.
-- Called for both client-side (TheSkillTree) and server-side (per-instance) skilltree data.
local function EnsureWandaSkillXP(skilltree)
    if skilltree ~= nil and skilltree.skillxp ~= nil and skilltree.skillxp["wanda"] == nil then
        skilltree.skillxp["wanda"] = 0
    end
end

AddComponentPostInit("skilltreeupdater", function(cmp, inst)
    if cmp.inst == nil then
        return
    end
    -- Initialize skillxp on every skilltreeupdater, both client and server.
    -- Client side: cmp.skilltree may be replaced later by TheSkillTree via
    -- playeractivated event, but it's harmless to init the temp instance too.
    EnsureWandaSkillXP(cmp.skilltree)
    if cmp.inst.prefab == "wanda" and not TheNet:IsDedicated() and cmp.inst == ThePlayer then
        -- Client wanda: TheSkillTree is set in onplayeractivated; hook it there.
        cmp.inst:ListenForEvent("playeractivated", function()
            EnsureWandaSkillXP(TheSkillTree)
        end)
    end
end)

local function WrapPocketWatchHeal(inst)
    if not TheWorld.ismastersim then
        return
    end
    if inst.components.pocketwatch == nil or inst.components.pocketwatch._wanda_wrapped then
        return
    end
    inst.components.pocketwatch._wanda_wrapped = true

    local old_DoCastSpell = inst.components.pocketwatch.DoCastSpell
    inst.components.pocketwatch.DoCastSpell = function(watch, doer, target, pos)
        local success, reason = old_DoCastSpell(watch, doer, target, pos)
        if success and util.IsWanda(doer) then
            local bonus = util.GetHealBonus(doer)
            if bonus > 0 and doer.components.oldager ~= nil then
                doer.components.oldager:OnTakeDamage(bonus / TUNING.OLDAGE_HEALTH_SCALE, false, "wanda_heal_bonus")
            end

            if util.HasSkill(doer, "wanda_team_heal") then
                for _, teammate in ipairs(util.FindNearbyTeammates(doer, TUNING.WANDA_SKILLTREE_MOD.TEAM_HEAL_RADIUS)) do
                    teammate.components.health:DoDelta(TUNING.WANDA_SKILLTREE_MOD.TEAM_HEAL_AMOUNT, true, watch.prefab)
                    if util.HasSkill(doer, "wanda_team_protect") then
                        util.ProtectForFrames(teammate, TUNING.WANDA_SKILLTREE_MOD.TEAM_PROTECT_FRAMES)
                    end
                end
            end
        end
        return success, reason
    end
end

AddPrefabPostInit("pocketwatch_heal", WrapPocketWatchHeal)

local function CanRenamePocketWatch(doer, target)
    return util.IsWanda(doer)
        and util.HasSkill(doer, "wanda_recall_rename")
        and target ~= nil
        and (target.prefab == "pocketwatch_recall" or target.prefab == "pocketwatch_portal")
end

local function EnsureWatchWriteable(inst)
    if inst.components.writeable == nil then
        inst:AddComponent("writeable")
    end
    if inst.components.writeable ~= nil then
        inst.components.writeable:SetDefaultWriteable(false)
        inst.components.writeable:SetAutomaticDescriptionEnabled(false)
        inst.components.writeable:SetOnWrittenFn(function(watch, text)
            watch.wanda_custom_name = text
        end)
    end
end

local function WrapRecallWatch(inst)
    if not TheWorld.ismastersim then
        return
    end

    EnsureWatchWriteable(inst)

    local old_OnSave = inst.OnSave
    inst.OnSave = function(inst, data)
        if old_OnSave ~= nil then
            old_OnSave(inst, data)
        end
        if inst.components.writeable ~= nil then
            data.wanda_recall_name = inst.components.writeable:GetText()
        end
        data.wanda_custom_name = inst.wanda_custom_name
        data.wanda_bond_userid = inst.wanda_bond_userid
        data.wanda_bond_name = inst.wanda_bond_name
    end

    local old_OnLoad = inst.OnLoad
    inst.OnLoad = function(inst, data)
        if old_OnLoad ~= nil then
            old_OnLoad(inst, data)
        end
        if data ~= nil then
            if data.wanda_recall_name ~= nil and inst.components.writeable ~= nil then
                inst.components.writeable:SetText(data.wanda_recall_name)
                inst.wanda_custom_name = data.wanda_recall_name
            end
            inst.wanda_custom_name = data.wanda_custom_name or inst.wanda_custom_name
            inst.wanda_bond_userid = data.wanda_bond_userid
            inst.wanda_bond_name = data.wanda_bond_name
        end
    end

    inst.displaynamefn = function(inst)
        local text = inst.components.writeable ~= nil and inst.components.writeable:GetText() or nil
        if text ~= nil and text ~= "" then
            return text
        end
        if inst.wanda_bond_name ~= nil then
            return (STRINGS.NAMES.POCKETWATCH_RECALL or "Backtrek Watch") .. " - " .. inst.wanda_bond_name
        end
        return nil
    end

    if inst.components.pocketwatch ~= nil and not inst.components.pocketwatch._wanda_recall_wrapped then
        inst.components.pocketwatch._wanda_recall_wrapped = true
        local old_DoCastSpell = inst.components.pocketwatch.DoCastSpell
        inst.components.pocketwatch.DoCastSpell = function(watch, doer, target, pos)
            if util.IsWanda(doer)
                and util.HasSkill(doer, "wanda_bond_mark")
                and watch.wanda_bond_userid ~= nil
            then
                local bonded = util.FindPlayerByUserid(watch.wanda_bond_userid)
                if bonded ~= nil and bonded:IsValid() and not bonded:HasTag("playerghost") then
                    local x, y, z = bonded.Transform:GetWorldPosition()
                    watch.components.rechargeable:Discharge(TUNING.POCKETWATCH_RECALL_COOLDOWN)
                    doer.sg.statemem.warpback = { dest_x = x, dest_y = y, dest_z = z }
                    return true
                end
            end
            return old_DoCastSpell(watch, doer, target, pos)
        end
    end
end

AddPrefabPostInit("pocketwatch_recall", WrapRecallWatch)

local function WrapPortalWatch(inst)
    if not TheWorld.ismastersim then
        return
    end

    EnsureWatchWriteable(inst)

    local old_OnSave = inst.OnSave
    inst.OnSave = function(inst, data)
        if old_OnSave ~= nil then
            old_OnSave(inst, data)
        end
        if inst.components.writeable ~= nil then
            data.wanda_recall_name = inst.components.writeable:GetText()
        end
        data.wanda_custom_name = inst.wanda_custom_name
    end

    local old_OnLoad = inst.OnLoad
    inst.OnLoad = function(inst, data)
        if old_OnLoad ~= nil then
            old_OnLoad(inst, data)
        end
        if data ~= nil then
            if data.wanda_recall_name ~= nil and inst.components.writeable ~= nil then
                inst.components.writeable:SetText(data.wanda_recall_name)
                inst.wanda_custom_name = data.wanda_recall_name
            end
            inst.wanda_custom_name = data.wanda_custom_name or inst.wanda_custom_name
        end
    end

    inst.displaynamefn = function(inst)
        local text = inst.components.writeable ~= nil and inst.components.writeable:GetText() or nil
        return text ~= nil and text ~= "" and text or nil
    end

    if inst.components.pocketwatch == nil or inst.components.pocketwatch._wanda_portal_wrapped then
        return
    end
    inst.components.pocketwatch._wanda_portal_wrapped = true
    local old_DoCastSpell = inst.components.pocketwatch.DoCastSpell

    inst.components.pocketwatch.DoCastSpell = function(watch, doer, target, pos)
        if util.IsWanda(doer)
            and util.HasSkill(doer, "wanda_portal_stable")
            and watch.components.recallmark ~= nil
            and watch.components.recallmark:IsMarked()
        then
            local recallmark = watch.components.recallmark
            if not Shard_IsWorldAvailable(recallmark.recall_worldid) then
                return false, "SHARD_UNAVAILABLE"
            end

            local pt = doer:GetPosition()
            local NOTENTCHECK_CANT_TAGS = { "FX", "INLIMBO" }
            local function noentcheckfn(checkpt)
                return not TheWorld.Map:IsPointNearHole(checkpt)
                    and #TheSim:FindEntities(checkpt.x, checkpt.y, checkpt.z, 1, nil, NOTENTCHECK_CANT_TAGS) == 0
            end
            local offset = FindWalkableOffset(pt, math.random() * TWOPI, 3 + math.random(), 16, false, true, noentcheckfn, true, true)
                or FindWalkableOffset(pt, math.random() * TWOPI, 5 + math.random(), 16, false, true, noentcheckfn, true, true)
                or FindWalkableOffset(pt, math.random() * TWOPI, 7 + math.random(), 16, false, true, noentcheckfn, true, true)
            if offset ~= nil then
                pt = pt + offset
            end

            local portal = SpawnPrefab("pocketwatch_portal_entrance")
            portal.Transform:SetPosition(pt:Get())
            portal:SpawnExit(recallmark.recall_worldid, recallmark.recall_x, recallmark.recall_y, recallmark.recall_z)
            watch.SoundEmitter:PlaySound("wanda1/wanda/portal_entrance_pre")
            watch.components.rechargeable:Discharge(TUNING.POCKETWATCH_RECALL_COOLDOWN)
            return true
        end
        return old_DoCastSpell(watch, doer, target, pos)
    end
end

AddPrefabPostInit("pocketwatch_portal", WrapPortalWatch)

AddPrefabPostInit("featherpencil", function(inst)
    inst:AddTag("wanda_watch_renamer")
end)

local WANDA_RENAME_WATCH = AddAction("WANDA_RENAME_WATCH", STRINGS.ACTIONS.WANDA_RENAME_WATCH, function(act)
    if act.invobject ~= nil
        and act.invobject.prefab == "featherpencil"
        and CanRenamePocketWatch(act.doer, act.target)
        and act.target.components.writeable ~= nil
    then
        if act.target.components.writeable:IsBeingWritten() then
            return false, "INUSE"
        end
        if CanEntitySeeTarget(act.doer, act.target) then
            act.target.components.writeable:BeginWriting(act.doer)
        end
        return true
    end
end)
WANDA_RENAME_WATCH.rmb = true
WANDA_RENAME_WATCH.priority = 9

AddComponentAction("USEITEM", "drawingtool", function(inst, doer, target, actions, right)
    if right
        and inst.prefab == "featherpencil"
        and CanRenamePocketWatch(doer, target)
    then
        table.insert(actions, ACTIONS.WANDA_RENAME_WATCH)
    end
end)

AddStategraphActionHandler("wilson", ActionHandler(ACTIONS.WANDA_RENAME_WATCH, "doshortaction"))
AddStategraphActionHandler("wilson_client", ActionHandler(ACTIONS.WANDA_RENAME_WATCH, "doshortaction"))

AddComponentPostInit("rechargeable", function(self)
    local old_Discharge = self.Discharge
    self.Discharge = function(self, charge, ...)
        if self.inst ~= nil and self.inst:HasTag("pocketwatch") then
            local owner = util.GetGrandOwner(self.inst)
            if util.IsWanda(owner) and util.HasSkill(owner, "wanda_watch_tune") then
                charge = charge * TUNING.WANDA_SKILLTREE_MOD.WATCH_COOLDOWN_MULT
            end
        end
        return old_Discharge(self, charge, ...)
    end
end)

local function AddAlarmWeaponHooks(inst)
    inst:AddTag("wanda_alarm_weapon")
    if not TheWorld.ismastersim then
        return
    end
    inst:DoTaskInTime(0, function()
        if inst.components.weapon == nil or inst.components.weapon._wanda_alarm_wrapped then
            return
        end
        inst.components.weapon._wanda_alarm_wrapped = true
        local old_onattack = inst.components.weapon.onattack
        inst.components.weapon:SetOnAttack(function(weapon, attacker, target, ...)
            if old_onattack ~= nil then
                old_onattack(weapon, attacker, target, ...)
            end
            if not util.IsWanda(attacker) or target == nil or target.components == nil or target.components.health == nil then
                return
            end
            local hat = attacker.components.inventory ~= nil and attacker.components.inventory:GetEquippedItem(EQUIPSLOTS.HEAD) or nil
            if hat ~= nil and hat.prefab == "voidclothhat" and util.HasSkill(attacker, "wanda_shadow_clock") then
                attacker.wanda_shadow_clock_stacks = math.min((attacker.wanda_shadow_clock_stacks or 0) + 1, 5)
                target.components.health:DoDelta(-TUNING.WANDA_SKILLTREE_MOD.SHADOW_PLANAR_DAMAGE, false, "wanda_shadow_clock", nil, attacker, true)
                if inst.components.weapon ~= nil then
                    inst.components.weapon:SetDamage(TUNING.POCKETWATCH_SHADOW_DAMAGE * (1 + attacker.wanda_shadow_clock_stacks * 0.05))
                end
            elseif hat ~= nil and hat.prefab == "lunarplanthat" and util.HasSkill(attacker, "wanda_lunar_clock") then
                local base_damage = inst.components.weapon ~= nil and inst.components.weapon.damage or TUNING.POCKETWATCH_SHADOW_DAMAGE
                target.components.health:DoDelta(-TUNING.WANDA_SKILLTREE_MOD.LUNAR_PLANAR_DAMAGE, false, "wanda_lunar_clock", nil, attacker, true)
                local x, y, z = target.Transform:GetWorldPosition()
                for _, ent in ipairs(TheSim:FindEntities(x, y, z, 3, { "_combat" }, { "INLIMBO", "player", "playerghost", "FX" })) do
                    if ent ~= target and ent.components.health ~= nil and not ent.components.health:IsDead() then
                        ent.components.combat:GetAttacked(attacker, base_damage * TUNING.WANDA_SKILLTREE_MOD.LUNAR_AOE_DAMAGE_MULT, weapon)
                    end
                end
            end
        end)
    end)
end

AddPrefabPostInit("pocketwatch_weapon", AddAlarmWeaponHooks)
AddPrefabPostInit("desperate_pocketwatch_weapon", AddAlarmWeaponHooks)

local WANDA_BOND_MARK = AddAction("WANDA_BOND_MARK", STRINGS.ACTIONS.WANDA_BOND_MARK, function(act)
    local watch = act.invobject
    local doer = act.doer
    local target = act.target
    if watch ~= nil and watch.prefab == "pocketwatch_recall"
        and util.IsWanda(doer)
        and util.HasSkill(doer, "wanda_bond_mark")
        and target ~= nil and target:HasTag("player")
    then
        watch.wanda_bond_userid = target.userid
        watch.wanda_bond_name = target:GetDisplayName()
        if watch.components.recallmark ~= nil then
            local x, y, z = target.Transform:GetWorldPosition()
            watch.components.recallmark:MarkPosition(x, y, z)
        end
        return true
    end
end)
WANDA_BOND_MARK.rmb = true
WANDA_BOND_MARK.priority = 8

AddComponentAction("USEITEM", "inventoryitem", function(inst, doer, target, actions)
    if inst.prefab == "pocketwatch_recall"
        and target ~= nil and target:HasTag("player")
        and util.IsWanda(doer)
        and util.HasSkill(doer, "wanda_bond_mark")
    then
        table.insert(actions, ACTIONS.WANDA_BOND_MARK)
    end
end)

AddStategraphActionHandler("wilson", ActionHandler(ACTIONS.WANDA_BOND_MARK, "give"))
AddStategraphActionHandler("wilson_client", ActionHandler(ACTIONS.WANDA_BOND_MARK, "give"))

local function TryFateRewind(target)
    if target == nil or target.userid == nil then
        return
    end
    for _, player in ipairs(AllPlayers) do
        if util.IsWanda(player) and util.HasSkill(player, "wanda_fate_rewind") then
            local watch = util.FindBondedRecallWatch(player, target.userid)
            if watch ~= nil then
                local x, y, z = target.Transform:GetWorldPosition()
                local fx = SpawnPrefab("attune_out_fx")
                if fx ~= nil then
                    fx.Transform:SetPosition(x, y, z)
                end
                target:DoTaskInTime(0.5, function()
                    if target:IsValid() and target:HasTag("playerghost") then
                        target:PushEvent("respawnfromghost", { source = watch })
                        if util.HasSkill(player, "wanda_team_protect") then
                            util.ProtectForFrames(target, TUNING.WANDA_SKILLTREE_MOD.TEAM_PROTECT_FRAMES)
                        end
                    end
                    if watch:IsValid() then
                        watch:Remove()
                    end
                end)
                return
            end
        end
    end
end

AddPlayerPostInit(function(inst)
    if not TheWorld.ismastersim then
        return
    end
    inst:ListenForEvent("ms_becameghost", TryFateRewind)
end)

AddStategraphPostInit("wilson", function(sg)
    local state = sg.states.pocketwatch_warpback
    if state ~= nil and state.timeline ~= nil then
        table.insert(state.timeline, 1, TimeEvent(1 * FRAMES, function(inst)
            if util.IsWanda(inst) and util.HasSkill(inst, "wanda_warp_iframe") then
                inst.sg:AddStateTag("noattack")
                inst.components.health:SetInvincible(true)
                inst.DynamicShadow:Enable(false)
            end
        end))

        local old_onenter = state.onenter
        state.onenter = function(inst, data, ...)
            if util.IsWanda(inst) and util.HasSkill(inst, "wanda_warp_shadow") then
                inst.wanda_last_warp_origin = inst:GetPosition()
            end
            if old_onenter ~= nil then
                old_onenter(inst, data, ...)
            end
        end
    end
end)

AddComponentPostInit("inventory", function(self, inst)
    local owner = self.inst or inst
    if owner ~= nil and owner.prefab == "wanda" then
        self.equipslots[EQUIPSLOTS.WANDA_TIMEBOX] = nil
    end
end)

AddClassPostConstruct("widgets/inventorybar", function(self, owner)
    if owner ~= nil and owner.prefab == "wanda" and self.AddEquipSlot ~= nil then
        self:AddEquipSlot(EQUIPSLOTS.WANDA_TIMEBOX, "images/inventoryimages.xml", "pocketwatch_parts.tex", 3.5)
    end
end)
