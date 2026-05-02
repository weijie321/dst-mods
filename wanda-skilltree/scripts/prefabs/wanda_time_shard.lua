local assets =
{
    Asset("ANIM", "anim/pocketwatch.zip"),
}

local function fn()
    local inst = CreateEntity()

    inst.entity:AddTransform()
    inst.entity:AddAnimState()
    inst.entity:AddNetwork()

    MakeInventoryPhysics(inst)

    inst.AnimState:SetBank("pocketwatch")
    inst.AnimState:SetBuild("pocketwatch")
    inst.AnimState:PlayAnimation("idle")
    inst.Transform:SetScale(0.65, 0.65, 0.65)

    inst:AddTag("molebait")

    MakeInventoryFloatable(inst, "small", 0.05, { 1.2, 0.75, 1.2 })

    inst.entity:SetPristine()

    if not TheWorld.ismastersim then
        return inst
    end

    inst:AddComponent("inspectable")
    inst:AddComponent("inventoryitem")
    inst.components.inventoryitem.imagename = "pocketwatch_parts"
    inst.components.inventoryitem.atlasname = "images/inventoryimages.xml"

    inst:AddComponent("stackable")
    inst.components.stackable.maxsize = TUNING.STACK_SIZE_SMALLITEM

    MakeHauntableLaunch(inst)

    return inst
end

return Prefab("wanda_time_shard", fn, assets)
