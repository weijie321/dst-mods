local Config = require("crashtrace.config")

local I18N = {}

local TERMS = {
    zh = {
        hook = {
            AddPlayerPostInit = "玩家初始化回调",
            AddPrefabPostInit = "实体初始化回调",
            AddPrefabPostInitAny = "任意实体初始化回调",
            AddComponentPostInit = "组件初始化回调",
            AddGamePostInit = "游戏初始化回调",
            AddSimPostInit = "模拟初始化回调",
            ListenForEvent = "事件监听",
            DoTaskInTime = "延时任务",
            DoPeriodicTask = "周期任务",
            native_lua_error = "原生 Lua 异常",
        },
        action = {
            player_post_init = "玩家初始化",
            prefab_post_init = "实体初始化",
            prefab_post_init_any = "任意实体初始化",
            component_post_init = "组件初始化",
            game_post_init = "游戏初始化",
            sim_post_init = "模拟初始化",
            event_listener = "事件监听触发",
            task_in_time = "延时任务触发",
            periodic_task = "周期任务触发",
            native_lua_error = "原生 Lua 异常",
            pick_action = "采集动作",
            attack_action = "攻击动作",
            equip_action = "装备动作",
            build_action = "建造动作",
        },
        event = {
            picked = "采集",
            death = "死亡",
            attacked = "被攻击",
            onremove = "移除",
            equip = "装备",
            unequip = "卸下",
            builditem = "制作",
            onbuilt = "建造完成",
            harvest = "收获",
            working = "作业",
        },
        prefab = {
            wilson = "威尔逊",
            willow = "薇洛",
            wolfgang = "沃尔夫冈",
            wendy = "温蒂",
            wx78 = "WX-78",
            wickerbottom = "薇克巴顿",
            woodie = "伍迪",
            wes = "韦斯",
            waxwell = "麦斯威尔",
            wathgrithr = "薇格弗德",
            webber = "韦伯",
            winona = "薇诺娜",
            wortox = "沃拓克斯",
            wormwood = "沃姆伍德",
            wurt = "沃特",
            walter = "沃尔特",
            wanda = "旺达",
            grass = "草",
            sapling = "树枝苗",
            reeds = "芦苇",
            berrybush = "浆果丛",
            berrybush2 = "浆果丛",
            berrybush_juicy = "多汁浆果丛",
            carrot_planted = "胡萝卜",
            flower = "花",
            flint = "燧石",
            rock1 = "岩石",
            evergreen = "常青树",
            deciduoustree = "桦栗树",
            marsh_bush = "尖刺灌木",
            cactus = "仙人掌",
            pickable = "可采集物",
            player = "玩家",
            game = "游戏",
            sim = "模拟器",
        },
        phrases = {
            unknown = "未知",
            trigger_pick = "玩家%s采集%s时触发",
            trigger_event = "%s 的事件 %s 触发",
            trigger_delayed = "%s 的延时任务触发",
            trigger_periodic = "%s 的周期任务触发",
            trigger_attack = "玩家%s攻击%s时触发",
            trigger_equip = "玩家%s装备%s时触发",
            trigger_build = "玩家%s制作或建造%s时触发",
        },
    },
    en = {
        hook = {
            AddPlayerPostInit = "player post init hook",
            AddPrefabPostInit = "prefab post init hook",
            AddPrefabPostInitAny = "global prefab post init hook",
            AddComponentPostInit = "component post init hook",
            AddGamePostInit = "game post init hook",
            AddSimPostInit = "sim post init hook",
            ListenForEvent = "event listener hook",
            DoTaskInTime = "delayed task hook",
            DoPeriodicTask = "periodic task hook",
            native_lua_error = "native lua error",
        },
        action = {
            player_post_init = "player post init",
            prefab_post_init = "prefab post init",
            prefab_post_init_any = "global prefab post init",
            component_post_init = "component post init",
            game_post_init = "game post init",
            sim_post_init = "sim post init",
            event_listener = "event listener fired",
            task_in_time = "delayed task fired",
            periodic_task = "periodic task fired",
            native_lua_error = "native lua error",
            pick_action = "pick action",
            attack_action = "attack action",
            equip_action = "equip action",
            build_action = "build action",
        },
        event = {
            picked = "picked",
            death = "death",
            attacked = "attacked",
            onremove = "removed",
            equip = "equip",
            unequip = "unequip",
            builditem = "build",
            onbuilt = "built",
            harvest = "harvest",
            working = "work",
        },
        prefab = {
            wilson = "Wilson",
            willow = "Willow",
            wolfgang = "Wolfgang",
            wendy = "Wendy",
            wx78 = "WX-78",
            wickerbottom = "Wickerbottom",
            woodie = "Woodie",
            wes = "Wes",
            waxwell = "Maxwell",
            wathgrithr = "Wigfrid",
            webber = "Webber",
            winona = "Winona",
            wortox = "Wortox",
            wormwood = "Wormwood",
            wurt = "Wurt",
            walter = "Walter",
            wanda = "Wanda",
            grass = "grass",
            sapling = "sapling",
            reeds = "reeds",
            berrybush = "berry bush",
            berrybush2 = "berry bush",
            berrybush_juicy = "juicy berry bush",
            carrot_planted = "carrot",
            flower = "flower",
            flint = "flint",
            rock1 = "rock",
            evergreen = "evergreen",
            deciduoustree = "deciduous tree",
            marsh_bush = "spiky bush",
            cactus = "cactus",
            pickable = "pickable",
            player = "player",
            game = "game",
            sim = "sim",
        },
        phrases = {
            unknown = "unknown",
            trigger_pick = "player %s triggered this by picking %s",
            trigger_event = "%s event %s triggered this",
            trigger_delayed = "%s delayed task triggered this",
            trigger_periodic = "%s periodic task triggered this",
            trigger_attack = "player %s triggered this by attacking %s",
            trigger_equip = "player %s triggered this by equipping %s",
            trigger_build = "player %s triggered this by building %s",
        },
    },
}

local function get_terms(group)
    local lang = Config.GetLanguage()
    return TERMS[lang] and TERMS[lang][group] or TERMS.zh[group]
end

local function localize(group, value)
    if type(value) ~= "string" or value == "" then
        return TERMS.zh.phrases.unknown
    end

    local terms = get_terms(group)
    return terms[value] or value
end

function I18N.LocalizeHook(value)
    return localize("hook", value)
end

function I18N.LocalizeAction(value)
    return localize("action", value)
end

function I18N.LocalizeEvent(value)
    return localize("event", value)
end

function I18N.LocalizePrefab(value)
    return localize("prefab", value)
end

function I18N.BuildTriggerSummary(report)
    local action = report.action or ""
    local event_name = report.event or ""
    local target = report.target or report.prefab or ""
    local actor = report.picker or report.player or ""
    local phrases = get_terms("phrases")

    if event_name == "picked" and target ~= "" then
        return string.format(phrases.trigger_pick, I18N.LocalizePrefab(actor), I18N.LocalizePrefab(target))
    end

    if action == "event_listener" and event_name ~= "" then
        return string.format(phrases.trigger_event, I18N.LocalizePrefab(target), I18N.LocalizeEvent(event_name))
    end

    if event_name == "attacked" and target ~= "" then
        return string.format(phrases.trigger_attack, I18N.LocalizePrefab(actor), I18N.LocalizePrefab(target))
    end

    if event_name == "equip" and target ~= "" then
        return string.format(phrases.trigger_equip, I18N.LocalizePrefab(actor), I18N.LocalizePrefab(target))
    end

    if event_name == "builditem" and target ~= "" then
        return string.format(phrases.trigger_build, I18N.LocalizePrefab(actor), I18N.LocalizePrefab(target))
    end

    if action == "task_in_time" then
        return string.format(phrases.trigger_delayed, I18N.LocalizePrefab(target))
    end

    if action == "periodic_task" then
        return string.format(phrases.trigger_periodic, I18N.LocalizePrefab(target))
    end

    return phrases.unknown
end

return I18N
