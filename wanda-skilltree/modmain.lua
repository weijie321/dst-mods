GLOBAL.setmetatable(env, { __index = function(_, key) return GLOBAL.rawget(GLOBAL, key) end })

modimport("scripts/wanda_skill_strings.lua")

EQUIPSLOTS.WANDA_TIMEBOX = TUNING.WANDA_SKILLTREE_TIMEBOX_SLOT or "wanda_timebox"

PrefabFiles = {
    "wanda_timebox",
    "wanda_time_decoy",
    "desperate_pocketwatch_weapon",
}

Assets = {
    Asset("SCRIPT", "scripts/prefabs/skilltree_wanda.lua"),
    Asset("ANIM", "anim/pocketwatch.zip"),
    Asset("ANIM", "anim/pocketwatch_weapon.zip"),
}

TUNING.WANDA_SKILLTREE_MOD = {
    TIMEBOX_SLOT = "wanda_timebox",
    WATCH_COOLDOWN_MULT = 0.75,
    TEAM_HEAL_RADIUS = 8,
    TEAM_HEAL_AMOUNT = 30,
    TEAM_PROTECT_FRAMES = 3,
    WARP_SPEED_MULT = 1.25,
    WARP_SPEED_TIME = 4,
    DECOY_DAMAGE = 50,
    SHADOW_PLANAR_DAMAGE = 20,
    LUNAR_PLANAR_DAMAGE = 20,
    LUNAR_AOE_DAMAGE_MULT = 0.3,
}

local function RegisterWandaSkillTree()
    local skilltree_defs = require("prefabs/skilltree_defs")
    if skilltree_defs.SKILLTREE_DEFS.wanda ~= nil then
        print("[Wanda Skilltree Expanded] wanda skilltree already exists; skip registration.")
        return
    end

    local BuildSkillsData = require("prefabs/skilltree_wanda")
    local data = BuildSkillsData(skilltree_defs.FN)
    if data ~= nil and data.SKILLS ~= nil then
        skilltree_defs.CreateSkillTreeFor("wanda", data.SKILLS)
        skilltree_defs.SKILLTREE_ORDERS.wanda = data.ORDERS
        if data.BACKGROUND_SETTINGS ~= nil then
            skilltree_defs.SKILLTREE_METAINFO.wanda.BACKGROUND_SETTINGS = data.BACKGROUND_SETTINGS
        end
        print("[Wanda Skilltree Expanded] registered wanda skilltree.")
    end
end

RegisterWandaSkillTree()

modimport("scripts/containers_wanda_timebox.lua")
modimport("scripts/wanda_skill_hooks.lua")

local Ingredient = GLOBAL.Ingredient
local TECH = GLOBAL.TECH

AddRecipe2(
    "wanda_timebox_1",
    { Ingredient("pocketwatch_parts", 1), Ingredient("boards", 2), Ingredient("nightmarefuel", 2) },
    TECH.SCIENCE_ONE,
    {
        atlas = "images/inventoryimages.xml",
        image = "pocketwatch_parts.tex",
        builder_tag = "clockmaker",
    },
    { "TOOLS", "MAGIC" }
)

AddRecipe2(
    "wanda_timebox_2",
    { Ingredient("wanda_timebox_1", 1), Ingredient("boards", 2), Ingredient("nightmarefuel", 2) },
    TECH.SCIENCE_TWO,
    {
        atlas = "images/inventoryimages.xml",
        image = "pocketwatch_parts.tex",
        builder_tag = "clockmaker",
        builder_skill = "wanda_timebox_2",
    },
    { "TOOLS", "MAGIC" }
)

AddRecipe2(
    "wanda_timebox_3",
    { Ingredient("wanda_timebox_2", 1), Ingredient("boards", 2), Ingredient("nightmarefuel", 2) },
    TECH.SCIENCE_TWO,
    {
        atlas = "images/inventoryimages.xml",
        image = "pocketwatch_parts.tex",
        builder_tag = "clockmaker",
        builder_skill = "wanda_timebox_3",
    },
    { "TOOLS", "MAGIC" }
)

AddRecipe2(
    "desperate_pocketwatch_weapon",
    { Ingredient("dreadstone", 2), Ingredient("horrorfuel", 2), Ingredient("pocketwatch_weapon", 1) },
    TECH.LOST,
    {
        atlas = "images/inventoryimages.xml",
        image = "pocketwatch_weapon.tex",
        builder_skill = "wanda_desperate_alarm",
    },
    { "WEAPONS", "MAGIC" }
)
