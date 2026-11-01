return function(t)
    local catalog = require("turf_collection_catalog")
    t.Assert("client_catalog_130", #catalog == 130)
    t.After(4, function()
        local x, _, z = ThePlayer.Transform:GetWorldPosition()
        local entities = TheSim:FindEntities(x, 0, z, 20)
        local items = {}
        for _, entity in ipairs(entities) do items[entity.prefab] = entity end
        for index, entry in ipairs(catalog) do
            local item = items["turf_" .. entry.name]
            local key = entry.name
            t.Assert(key .. ".client_item", item ~= nil and item.tile == WORLD_TILES[entry.tile])
            local inv = item ~= nil and item.replica.inventoryitem or nil
            local image = "turf_" .. entry.name .. ".tex"
            local atlas = resolvefilepath("images/inventoryimages/turf_" .. entry.name .. ".xml")
            local actual_atlas = inv ~= nil and inv:GetAtlas() or nil
            local actual_image = inv ~= nil and inv:GetImage() or nil
            -- Replica 的网络覆盖为 net_hash；没有覆盖时返回默认文件名。
            local atlas_matches = actual_atlas == hash(atlas)
                or (type(actual_atlas) == "string" and resolvefilepath(actual_atlas) == atlas)
            local image_matches = actual_image == hash(image) or actual_image == image
            local contains = TheSim:AtlasContains(atlas, image)
            t.Assert(key .. ".client_icon", inv ~= nil
                and atlas_matches and image_matches and contains,
                {atlas = actual_atlas, image = actual_image, expected_atlas = atlas,
                    atlas_hash = hash(atlas), image_hash = hash(image), contains = contains})
            t.Assert(key .. ".client_anim", item ~= nil and item.AnimState:IsCurrentAnimation(entry.turf.anim))
            local col, row = (index - 1) % 13, math.floor((index - 1) / 13)
            t.Assert(key .. ".client_tile", TheWorld.Map:GetTileAtPoint(x + (col - 6) * 4, 0, z + (row - 4) * 4) == WORLD_TILES[entry.tile])
        end
        t.Assert("client_crafting_filter", CRAFTING_FILTERS.TURF_COLLECTION ~= nil)
        TheCamera:SetDistance(60)
        t.After(30, function() t.Done("130种真实客户端地皮、网络物品、图标和动画检查完成") end)
    end)
end
