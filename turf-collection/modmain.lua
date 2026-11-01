modimport("scripts/turf_collection_tiles.lua")

local G = GLOBAL
local catalog = require("turf_collection_catalog")
Assets = require("turf_collection_assets")
modimport("scripts/turf_collection_icons.lua")

local first = "turf_" .. catalog[1].name
G.STRINGS.UI.CRAFTING_FILTERS.TURF_COLLECTION = "地皮合集"
AddRecipeFilter({name = "TURF_COLLECTION", atlas = "images/inventoryimages/" .. first .. ".xml", image = first .. ".tex"})

for _, tile in ipairs(catalog) do
    local prefab = "turf_" .. tile.name
    local atlas = "images/inventoryimages/" .. prefab .. ".xml"
    local stringkey = string.upper(prefab)
    G.STRINGS.NAMES[stringkey] = tile.source_title .. "·" .. tile.display
    G.STRINGS.RECIPE_DESC[stringkey] = "制作4块" .. tile.display .. "。"
    G.STRINGS.CHARACTERS.GENERIC.DESCRIBE[stringkey] = "来自" .. tile.source_title .. "的地皮。"
    AddRecipe2(prefab, {G.Ingredient("cutgrass", 1), G.Ingredient("rocks", 1)}, G.TECH.NONE,
        {numtogive = 4, atlas = atlas, image = prefab .. ".tex"}, {"TURF_COLLECTION"})
end
