local AGE_X = -160
local WATCH_X = -80
local WARP_X = 0
local TEAM_X = 80
local AFFINITY_X = 160
local TOP_Y = 176
local STEP_Y = 35

local ORDERS =
{
    { "age", { AGE_X, TOP_Y + 30 } },
    { "watch", { WATCH_X, TOP_Y + 30 } },
    { "warp", { WARP_X, TOP_Y + 30 } },
    { "team", { TEAM_X, TOP_Y + 30 } },
    { "allegiance", { AFFINITY_X, TOP_Y + 30 } },
}

local function ApplyWandaSkill(inst)
    if inst ~= nil and inst.prefab == "wanda" and inst.ApplyWandaSkillTreeBonuses ~= nil then
        inst:ApplyWandaSkillTreeBonuses()
    end
end

local function BuildSkillsData(SkillTreeFns)
    local W = STRINGS.SKILLTREE.WANDA
    local skills =
    {
        wanda_age_max_1 =
        {
            title = W.WANDA_AGE_MAX_1_TITLE,
            desc = W.WANDA_AGE_MAX_1_DESC,
            icon = "wilson_beard_insulation_1",
            pos = { AGE_X - 20, TOP_Y },
            group = "age",
            tags = { "age", "age_max" },
            root = true,
            connects = { "wanda_age_max_2" },
            defaultfocus = true,
            onactivate = ApplyWandaSkill,
            ondeactivate = ApplyWandaSkill,
        },
        wanda_age_max_2 =
        {
            title = W.WANDA_AGE_MAX_2_TITLE,
            desc = W.WANDA_AGE_MAX_2_DESC,
            icon = "wilson_beard_insulation_2",
            pos = { AGE_X - 20, TOP_Y - STEP_Y },
            group = "age",
            tags = { "age", "age_max" },
            connects = { "wanda_age_max_3" },
            onactivate = ApplyWandaSkill,
            ondeactivate = ApplyWandaSkill,
        },
        wanda_age_max_3 =
        {
            title = W.WANDA_AGE_MAX_3_TITLE,
            desc = W.WANDA_AGE_MAX_3_DESC,
            icon = "wilson_beard_insulation_3",
            pos = { AGE_X - 20, TOP_Y - STEP_Y * 2 },
            group = "age",
            tags = { "age", "age_max" },
            onactivate = ApplyWandaSkill,
            ondeactivate = ApplyWandaSkill,
        },
        wanda_heal_bonus_1 =
        {
            title = W.WANDA_HEAL_BONUS_1_TITLE,
            desc = W.WANDA_HEAL_BONUS_1_DESC,
            icon = "wilson_alchemy_gem_1",
            pos = { AGE_X + 20, TOP_Y },
            group = "age",
            tags = { "age", "heal_bonus" },
            root = true,
            connects = { "wanda_heal_bonus_2" },
        },
        wanda_heal_bonus_2 =
        {
            title = W.WANDA_HEAL_BONUS_2_TITLE,
            desc = W.WANDA_HEAL_BONUS_2_DESC,
            icon = "wilson_alchemy_gem_2",
            pos = { AGE_X + 20, TOP_Y - STEP_Y },
            group = "age",
            tags = { "age", "heal_bonus" },
            connects = { "wanda_heal_bonus_3" },
        },
        wanda_heal_bonus_3 =
        {
            title = W.WANDA_HEAL_BONUS_3_TITLE,
            desc = W.WANDA_HEAL_BONUS_3_DESC,
            icon = "wilson_alchemy_gem_3",
            pos = { AGE_X + 20, TOP_Y - STEP_Y * 2 },
            group = "age",
            tags = { "age", "heal_bonus" },
        },
        wanda_old_calm =
        {
            title = W.WANDA_OLD_CALM_TITLE,
            desc = W.WANDA_OLD_CALM_DESC,
            icon = "wolfgang_mighty_3",
            pos = { AGE_X - 20, TOP_Y - STEP_Y * 3 - 10 },
            group = "age",
            tags = { "age", "old_calm" },
            root = true,
            connects = {},
            onactivate = ApplyWandaSkill,
            ondeactivate = ApplyWandaSkill,
        },
        wanda_planar_defense_lock =
        {
            desc = STRINGS.SKILLTREE.ALLEGIANCE_LOCK_2_DESC,
            icon = "wilson_lock_1",
            pos = { AGE_X + 15, TOP_Y - STEP_Y * 3 - 10 },
            group = "age",
            tags = { "age", "lock" },
            root = true,
            lock_open = function(prefabname, activatedskills)
                return SkillTreeFns.CountTags(prefabname, "allegiance", activatedskills) > 0
            end,
            connects = { "wanda_planar_defense" },
        },
        wanda_planar_defense =
        {
            title = W.WANDA_PLANAR_DEFENSE_TITLE,
            desc = W.WANDA_PLANAR_DEFENSE_DESC,
            icon = "wilson_favor_shadow",
            pos = { AGE_X + 50, TOP_Y - STEP_Y * 3 - 10 },
            group = "age",
            tags = { "age", "planar_defense" },
            locks = { "wanda_planar_defense_lock" },
            onactivate = ApplyWandaSkill,
            ondeactivate = ApplyWandaSkill,
        },

        wanda_timebox_1 =
        {
            title = W.WANDA_TIMEBOX_1_TITLE,
            desc = W.WANDA_TIMEBOX_1_DESC,
            icon = "winona_catapult_1",
            pos = { WATCH_X - 20, TOP_Y },
            group = "watch",
            tags = { "watch", "timebox" },
            root = true,
            connects = { "wanda_timebox_2" },
            onactivate = ApplyWandaSkill,
            ondeactivate = ApplyWandaSkill,
        },
        wanda_timebox_2 =
        {
            title = W.WANDA_TIMEBOX_2_TITLE,
            desc = W.WANDA_TIMEBOX_2_DESC,
            icon = "winona_catapult_2",
            pos = { WATCH_X - 20, TOP_Y - STEP_Y },
            group = "watch",
            tags = { "watch", "timebox" },
            connects = { "wanda_timebox_3" },
            onactivate = ApplyWandaSkill,
            ondeactivate = ApplyWandaSkill,
        },
        wanda_timebox_3 =
        {
            title = W.WANDA_TIMEBOX_3_TITLE,
            desc = W.WANDA_TIMEBOX_3_DESC,
            icon = "winona_catapult_3",
            pos = { WATCH_X - 20, TOP_Y - STEP_Y * 2 },
            group = "watch",
            tags = { "watch", "timebox" },
            onactivate = ApplyWandaSkill,
            ondeactivate = ApplyWandaSkill,
        },
        wanda_watch_tune =
        {
            title = W.WANDA_WATCH_TUNE_TITLE,
            desc = W.WANDA_WATCH_TUNE_DESC,
            icon = "wilson_alchemy_1",
            pos = { WATCH_X + 20, TOP_Y },
            group = "watch",
            tags = { "watch", "tune" },
            root = true,
        },
        wanda_desperate_alarm =
        {
            title = W.WANDA_DESPERATE_ALARM_TITLE,
            desc = W.WANDA_DESPERATE_ALARM_DESC,
            icon = "wilson_alchemy_iky_1",
            pos = { WATCH_X + 20, TOP_Y - STEP_Y },
            group = "watch",
            tags = { "watch", "alarm" },
            root = true,
        },

        wanda_warp_speed =
        {
            title = W.WANDA_WARP_SPEED_TITLE,
            desc = W.WANDA_WARP_SPEED_DESC,
            icon = "wormwood_quick_selffertilizer",
            pos = { WARP_X, TOP_Y },
            group = "warp",
            tags = { "warp" },
            root = true,
            connects = { "wanda_warp_shadow", "wanda_warp_iframe" },
        },
        wanda_recall_rename =
        {
            title = W.WANDA_RECALL_RENAME_TITLE,
            desc = W.WANDA_RECALL_RENAME_DESC,
            icon = "wilson_torch_brightness_1",
            pos = { WARP_X - 25, TOP_Y - STEP_Y },
            group = "warp",
            tags = { "warp", "recall" },
            root = true,
            connects = { "wanda_portal_stable" },
        },
        wanda_warp_shadow =
        {
            title = W.WANDA_WARP_SHADOW_TITLE,
            desc = W.WANDA_WARP_SHADOW_DESC,
            icon = "wortox_souldecoy_1",
            pos = { WARP_X + 25, TOP_Y - STEP_Y },
            group = "warp",
            tags = { "warp", "decoy" },
        },
        wanda_portal_stable =
        {
            title = W.WANDA_PORTAL_STABLE_TITLE,
            desc = W.WANDA_PORTAL_STABLE_DESC,
            icon = "wilson_alchemy_gem_2",
            pos = { WARP_X - 25, TOP_Y - STEP_Y * 2 },
            group = "warp",
            tags = { "warp", "portal" },
        },
        wanda_warp_iframe =
        {
            title = W.WANDA_WARP_IFRAME_TITLE,
            desc = W.WANDA_WARP_IFRAME_DESC,
            icon = "wilson_torch_time_3",
            pos = { WARP_X + 25, TOP_Y - STEP_Y * 2 },
            group = "warp",
            tags = { "warp", "iframe" },
        },

        wanda_team_heal =
        {
            title = W.WANDA_TEAM_HEAL_TITLE,
            desc = W.WANDA_TEAM_HEAL_DESC,
            icon = "wendy_sisturn_1",
            pos = { TEAM_X, TOP_Y },
            group = "team",
            tags = { "team" },
            root = true,
            connects = { "wanda_team_protect", "wanda_bond_mark" },
        },
        wanda_team_protect =
        {
            title = W.WANDA_TEAM_PROTECT_TITLE,
            desc = W.WANDA_TEAM_PROTECT_DESC,
            icon = "wendy_sisturn_2",
            pos = { TEAM_X - 20, TOP_Y - STEP_Y },
            group = "team",
            tags = { "team", "protect" },
        },
        wanda_bond_mark =
        {
            title = W.WANDA_BOND_MARK_TITLE,
            desc = W.WANDA_BOND_MARK_DESC,
            icon = "wendy_ghostflower_1",
            pos = { TEAM_X + 20, TOP_Y - STEP_Y },
            group = "team",
            tags = { "team", "bond" },
            connects = { "wanda_fate_rewind" },
        },
        wanda_fate_rewind =
        {
            title = W.WANDA_FATE_REWIND_TITLE,
            desc = W.WANDA_FATE_REWIND_DESC,
            icon = "wendy_abigail_3",
            pos = { TEAM_X + 20, TOP_Y - STEP_Y * 2 },
            group = "team",
            tags = { "team", "rewind" },
        },

        wanda_allegiance_lock_shadow_boss =
        {
            desc = STRINGS.SKILLTREE.ALLEGIANCE_LOCK_2_DESC,
            icon = "wilson_lock_1",
            pos = { AFFINITY_X - 20, TOP_Y },
            group = "allegiance",
            tags = { "allegiance", "lock" },
            root = true,
            lock_open = function(_, _, readonly)
                return readonly and "question" or TheGenericKV:GetKV("fuelweaver_killed") == "1"
            end,
            connects = { "wanda_allegiance_shadow" },
        },
        wanda_allegiance_lock_no_lunar =
        {
            desc = STRINGS.SKILLTREE.ALLEGIANCE_LOCK_5_DESC,
            icon = "wilson_lock_2",
            pos = { AFFINITY_X - 20, TOP_Y - STEP_Y },
            group = "allegiance",
            tags = { "allegiance", "lock" },
            root = true,
            lock_open = function(prefabname, activatedskills)
                return SkillTreeFns.CountTags(prefabname, "lunar_favor", activatedskills) == 0 or nil
            end,
            connects = { "wanda_allegiance_shadow" },
        },
        wanda_allegiance_shadow =
        {
            title = W.WANDA_ALLEGIANCE_SHADOW_TITLE,
            desc = W.WANDA_ALLEGIANCE_SHADOW_DESC,
            icon = "wilson_favor_shadow",
            pos = { AFFINITY_X - 20, TOP_Y - STEP_Y * 2 },
            group = "allegiance",
            tags = { "allegiance", "shadow_favor" },
            locks = { "wanda_allegiance_lock_shadow_boss", "wanda_allegiance_lock_no_lunar" },
            connects = { "wanda_shadow_clock" },
            onactivate = ApplyWandaSkill,
            ondeactivate = ApplyWandaSkill,
        },
        wanda_shadow_clock =
        {
            title = W.WANDA_SHADOW_CLOCK_TITLE,
            desc = W.WANDA_SHADOW_CLOCK_DESC,
            icon = "wilson_favor_shadow",
            pos = { AFFINITY_X - 20, TOP_Y - STEP_Y * 3 },
            group = "allegiance",
            tags = { "allegiance", "shadow_clock" },
        },

        wanda_allegiance_lock_lunar_boss =
        {
            desc = STRINGS.SKILLTREE.ALLEGIANCE_LOCK_3_DESC,
            icon = "wilson_lock_1",
            pos = { AFFINITY_X + 20, TOP_Y },
            group = "allegiance",
            tags = { "allegiance", "lock" },
            root = true,
            lock_open = function(_, _, readonly)
                return readonly and "question" or TheGenericKV:GetKV("celestialchampion_killed") == "1"
            end,
            connects = { "wanda_allegiance_lunar" },
        },
        wanda_allegiance_lock_no_shadow =
        {
            desc = STRINGS.SKILLTREE.ALLEGIANCE_LOCK_4_DESC,
            icon = "wilson_lock_2",
            pos = { AFFINITY_X + 20, TOP_Y - STEP_Y },
            group = "allegiance",
            tags = { "allegiance", "lock" },
            root = true,
            lock_open = function(prefabname, activatedskills)
                return SkillTreeFns.CountTags(prefabname, "shadow_favor", activatedskills) == 0 or nil
            end,
            connects = { "wanda_allegiance_lunar" },
        },
        wanda_allegiance_lunar =
        {
            title = W.WANDA_ALLEGIANCE_LUNAR_TITLE,
            desc = W.WANDA_ALLEGIANCE_LUNAR_DESC,
            icon = "wilson_favor_lunar",
            pos = { AFFINITY_X + 20, TOP_Y - STEP_Y * 2 },
            group = "allegiance",
            tags = { "allegiance", "lunar_favor" },
            locks = { "wanda_allegiance_lock_lunar_boss", "wanda_allegiance_lock_no_shadow" },
            connects = { "wanda_lunar_clock" },
            onactivate = ApplyWandaSkill,
            ondeactivate = ApplyWandaSkill,
        },
        wanda_lunar_clock =
        {
            title = W.WANDA_LUNAR_CLOCK_TITLE,
            desc = W.WANDA_LUNAR_CLOCK_DESC,
            icon = "wilson_favor_lunar",
            pos = { AFFINITY_X + 20, TOP_Y - STEP_Y * 3 },
            group = "allegiance",
            tags = { "allegiance", "lunar_clock" },
        },
    }

    return {
        SKILLS = skills,
        ORDERS = ORDERS,
    }
end

return BuildSkillsData
