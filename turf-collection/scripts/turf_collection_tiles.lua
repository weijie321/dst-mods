local catalog = require("turf_collection_catalog")
for _, tile in ipairs(catalog) do
    if GLOBAL.WORLD_TILES[tile.tile] == nil then
        AddTile(tile.tile, "LAND", {ground_name = tile.tile}, tile.ground, tile.mini, tile.turf)
    end
end
