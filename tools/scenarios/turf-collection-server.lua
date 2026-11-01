local catalog = require("turf_collection_catalog")
local groundtiles = require("worldtiledefs")
TEST.Assert("catalog_130", #catalog == 130, #catalog)
local sources, ids = {}, {}
local pt = Vector3(TheWorld.Map:GetTileCenterPoint(0, 0, 0))
local tx, ty = TheWorld.Map:GetTileCoordsAtPoint(pt:Get())
local oldtile = TheWorld.Map:GetTile(tx, ty)
for _, entity in ipairs(TheSim:FindEntities(pt.x, 0, pt.z, 4)) do
    if entity ~= TheWorld and not entity:HasTag("player") then entity:Remove() end
end
local fork = SpawnPrefab("pitchfork")
local player = SpawnPrefab("wilson")
player.Transform:SetPosition(pt.x + 4, 0, pt.z)
for _, entry in ipairs(catalog) do
    local key = entry.name
    local prefab = "turf_" .. key
    local id = WORLD_TILES[entry.tile]
    sources[entry.source] = true
    TEST.Assert(key .. ".registered", id ~= nil and not ids[id] and groundtiles.turf[id].name == key)
    ids[id] = true
    TEST.Assert(key .. ".standalone", WORLD_TILES[entry.original] == nil)
    local recipe = AllRecipes[prefab]
    TEST.Assert(key .. ".recipe", recipe ~= nil and recipe.numtogive == 4 and #recipe.ingredients == 2
        and recipe.ingredients[1].type == "cutgrass" and recipe.ingredients[1].amount == 1
        and recipe.ingredients[2].type == "rocks" and recipe.ingredients[2].amount == 1)
    player.components.inventory:GiveItem(SpawnPrefab("cutgrass"))
    player.components.inventory:GiveItem(SpawnPrefab("rocks"))
    local built = player.components.builder:DoBuild(prefab)
    local product = player.components.inventory:FindItem(function(entity) return entity.prefab == prefab end)
    TEST.Assert(key .. ".craft", built == true and product ~= nil and product.components.stackable:StackSize() == 4
        and not player.components.inventory:Has("cutgrass", 1) and not player.components.inventory:Has("rocks", 1))
    if product then product:Remove() end
    local item = SpawnPrefab(prefab)
    TEST.Assert(key .. ".spawn", item ~= nil and item.tile == id and item.components.deployable ~= nil)
    item.components.stackable:SetStackSize(2)
    local saved = item:GetSaveRecord()
    local restored = SpawnSaveRecord(saved)
    TEST.Assert(key .. ".item_reload", restored ~= nil and restored.tile == id and restored.components.stackable:StackSize() == 2)
    restored:Remove()
    TheWorld.Map:SetTile(tx, ty, WORLD_TILES.DIRT)
    TheWorld.components.undertile:ClearTileUnderneath(tx, ty)
    local allowed = item.components.deployable:CanDeploy(pt, nil, player)
    local deployed = allowed and item.components.deployable:Deploy(pt, player)
    TEST.Assert(key .. ".deploy", deployed == true and TheWorld.Map:GetTile(tx, ty) == id
        and item:IsValid() and item.components.stackable:StackSize() == 1)
    local dug = fork.components.terraformer:Terraform(pt)
    local drop
    for _, entity in ipairs(TheSim:FindEntities(pt.x, 0, pt.z, 6)) do
        if entity.prefab == prefab and entity ~= item then drop = entity; break end
    end
    TEST.Assert(key .. ".dig", dug == true and TheWorld.Map:GetTile(tx, ty) == WORLD_TILES.DIRT and drop ~= nil)
    if drop then drop:Remove() end
    item:Remove()
end
local count = 0
for _ in pairs(sources) do count = count + 1 end
TEST.Assert("sources_11", count == 11, count)
fork:Remove()
player:Remove()
TheWorld.Map:SetTile(tx, ty, oldtile)
TEST.Done("130种地皮独立注册、原版材料配方、物品保存恢复、铺设与挖回完成")
