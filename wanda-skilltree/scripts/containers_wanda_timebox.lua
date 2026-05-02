local containers = require("containers")

local params = containers.params

local function MakeSlotGrid(cols, rows)
    local slotpos = {}
    local spacing = 75
    local x0 = -spacing * (cols - 1) / 2
    local y0 = spacing * (rows - 1) / 2
    for y = 1, rows do
        for x = 1, cols do
            table.insert(slotpos, Vector3(x0 + (x - 1) * spacing, y0 - (y - 1) * spacing, 0))
        end
    end
    return slotpos
end

local function MakeTimeBoxParams(cols, rows)
    return {
        widget = {
            slotpos = MakeSlotGrid(cols, rows),
            animbank = "ui_chest_3x3",
            animbuild = "ui_chest_3x3",
            pos = Vector3(0, 200, 0),
            side_align_tip = 160,
        },
        type = "pack",
        itemtestfn = function(_, item)
            return item ~= nil and item:HasTag("pocketwatch")
        end,
    }
end

params.wanda_timebox_1 = MakeTimeBoxParams(2, 2)
params.wanda_timebox_2 = MakeTimeBoxParams(3, 3)
params.wanda_timebox_3 = MakeTimeBoxParams(4, 4)
