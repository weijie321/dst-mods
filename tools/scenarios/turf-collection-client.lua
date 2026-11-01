return function(t)
    local catalog = require("turf_collection_catalog")
    local corrected_icons = {
        tc_3609964985_hmr_cherry_flower = "images/inventoryimages/hmr_cherry_flower_turf.tex",
        tc_3609964985_hmr_cherry_grass = "images/inventoryimages/hmr_cherry_grass_turf.tex",
        tc_3544387985_tbat_turf_water_lily_cat = "atbooks1/images/inventoryimages/tbat_turf_water_lily_cat_leaf.tex",
    }
    t.Assert("client_catalog_130", #catalog == 130)
    t.Assert("client_display_name", STRINGS.UI.CRAFTING_FILTERS.TURF_COLLECTION == "321自用dp")
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
            if corrected_icons[key] ~= nil then
                t.Assert(key .. ".client_icon_source", contains and atlas_matches and image_matches
                    and entry.icon_source ~= nil and entry.icon_source.file == corrected_icons[key]
                    and not entry.icon_preview, entry.icon_source)
            end
            t.Assert(key .. ".client_anim", item ~= nil and item.AnimState:IsCurrentAnimation(entry.turf.anim))
            local col, row = (index - 1) % 13, math.floor((index - 1) / 13)
            t.Assert(key .. ".client_tile", TheWorld.Map:GetTileAtPoint(x + (col - 6) * 4, 0, z + (row - 4) * 4) == WORLD_TILES[entry.tile])
        end
        t.Assert("client_crafting_filter", CRAFTING_FILTERS.TURF_COLLECTION ~= nil)
        local hud = ThePlayer.HUD.controls.craftingmenu
        local menu = hud.craftingmenu
        local atlas = resolvefilepath("images/crafting_menu.xml")
        t.Assert("client_crafting_vanilla_atlas", resolvefilepath(CRAFTING_ATLAS) == atlas
            and TheSim:AtlasContains(atlas, "backing.tex"), {atlas = CRAFTING_ATLAS})
        local backing
        for child in pairs(menu.frame.children) do
            if child.texture == "backing.tex" then backing = child end
        end
        t.Assert("client_crafting_frame", backing ~= nil and backing.atlas == atlas,
            {atlas = backing ~= nil and backing.atlas or "missing"})
        local button = menu.filter_buttons.TURF_COLLECTION
        local width, height = button.filter_img:GetScaledSize()
        t.Assert("client_crafting_filter_size", width > 0 and width <= 64
            and height > 0 and height <= 64, {width = width, height = height})
        hud:Open()
        menu:SelectFilter("TURF_COLLECTION", true)
        t.After(1, function()
            t.Assert("client_crafting_open_catalog", hud:IsCraftingOpen()
                and menu.current_filter_name == "TURF_COLLECTION"
                and #menu.filtered_recipes == 130, {recipes = #menu.filtered_recipes})
            for _, data in ipairs(menu.filtered_recipes) do
                menu:PopulateRecipeDetailPanel(data)
                local image = menu.details_root.skins_spinner.spinner.fgimage
                local w, h = image:GetSize()
                t.Assert(data.recipe.product:sub(6) .. ".client_recipe_preview",
                    w > 0 and w <= 64 and h > 0 and h <= 64,
                    {width = w, height = h, atlas = image.atlas, image = image.texture})
            end
            local prefab = "turf_tc_1289779251_cherrift"
            menu:PopulateRecipeDetailPanel(hud:GetRecipeState(prefab))
            menu.details_root.build_button_root.button.onclick()
            t.After(3, function()
                local count = 0
                for _, item in pairs(ThePlayer.replica.inventory:GetItems()) do
                    if item.prefab == prefab then count = count + item.replica.stackable:StackSize() end
                end
                t.Assert("client_crafting_build_from_preview", count == 4, {count = count})
                hud:Close()
                t.After(0.5, function()
                    hud:Open()
                    menu:SelectFilter("TURF_COLLECTION", true)
                    menu:PopulateRecipeDetailPanel(hud:GetRecipeState(prefab))
                    local w, h = menu.details_root.skins_spinner.spinner.fgimage:GetSize()
                    t.Assert("client_crafting_reselect_preview", w <= 64 and h <= 64
                        and hud:IsCraftingOpen(), {width = w, height = h})
                end)
            end)
        end)
        TheCamera:SetDistance(60)
        t.After(30, function() t.Done("130种真实客户端地皮、网络物品、图标和动画检查完成") end)
    end)
end
