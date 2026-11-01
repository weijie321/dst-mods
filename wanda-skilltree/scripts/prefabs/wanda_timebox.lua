local assets =
{
    Asset("ANIM", "anim/pocketwatch.zip"),
}

local function CanEquipTimeBox(inst, owner)
    return owner ~= nil
        and owner.prefab == "wanda"
        and owner.components.skilltreeupdater ~= nil
        and owner.components.skilltreeupdater:IsActivated(inst.required_skill)
end

local function onequip(inst, owner)
    if not CanEquipTimeBox(inst, owner) then
        owner:DoTaskInTime(0, function()
            if owner.components.inventory ~= nil and owner.components.inventory:GetEquippedItem(EQUIPSLOTS.WANDA_TIMEBOX) == inst then
                owner.components.inventory:Unequip(EQUIPSLOTS.WANDA_TIMEBOX)
                owner.components.inventory:GiveItem(inst)
            end
        end)
    end
end

local function onunequip(inst, owner)
    if inst.components.container ~= nil then
        inst.components.container:Close(owner)
    end
end

local function MakeTimeBox(name, required_skill)
    local function fn()
        local inst = CreateEntity()

        inst.entity:AddTransform()
        inst.entity:AddAnimState()
        inst.entity:AddNetwork()

        MakeInventoryPhysics(inst)

        inst.AnimState:SetBank("pocketwatch")
        inst.AnimState:SetBuild("pocketwatch_marble")
        inst.AnimState:PlayAnimation("idle")

        inst:AddTag("wanda_timebox")
        inst:AddTag("portableitem")

        MakeInventoryFloatable(inst, "small", 0.05, { 1.2, 0.75, 1.2 })

        inst.entity:SetPristine()

        if not TheWorld.ismastersim then
            return inst
        end

        inst.required_skill = required_skill

        inst:AddComponent("inspectable")

        inst:AddComponent("inventoryitem")
        inst.components.inventoryitem.imagename = "pocketwatch_parts"
        inst.components.inventoryitem.atlasname = "images/inventoryimages.xml"

        inst:AddComponent("equippable")
        inst.components.equippable.equipslot = EQUIPSLOTS.WANDA_TIMEBOX
        inst.components.equippable:SetOnEquip(onequip)
        inst.components.equippable:SetOnUnequip(onunequip)

        inst:AddComponent("container")
        inst.components.container:WidgetSetup(name)

        MakeHauntableLaunch(inst)

        return inst
    end

    return Prefab(name, fn, assets)
end

return MakeTimeBox("wanda_timebox_1", "wanda_timebox_1"),
    MakeTimeBox("wanda_timebox_2", "wanda_timebox_2"),
    MakeTimeBox("wanda_timebox_3", "wanda_timebox_3")
