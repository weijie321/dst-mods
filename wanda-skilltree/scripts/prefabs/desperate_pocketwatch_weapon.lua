local assets =
{
    Asset("ANIM", "anim/pocketwatch_weapon.zip"),
}

local prefabs =
{
    "pocketwatch_weapon_fx",
}

local function onequip(inst, owner)
    owner.AnimState:OverrideSymbol("swap_object", "pocketwatch_weapon", "swap_object")
    owner.AnimState:Show("ARM_carry")
    owner.AnimState:Hide("ARM_normal")
end

local function onunequip(inst, owner)
    owner.AnimState:Hide("ARM_carry")
    owner.AnimState:Show("ARM_normal")
end

local function onattack(inst, attacker)
    inst.SoundEmitter:PlaySound("wanda2/characters/wanda/watch/weapon/shadow_attack")
    if inst.components.fueled ~= nil and not inst.components.fueled:IsEmpty() then
        inst.components.fueled:DoDelta(-TUNING.TINY_FUEL)
    end
end

local function fn()
    local inst = CreateEntity()

    inst.entity:AddTransform()
    inst.entity:AddAnimState()
    inst.entity:AddSoundEmitter()
    inst.entity:AddNetwork()

    MakeInventoryPhysics(inst)

    inst:AddTag("pocketwatch")
    inst:AddTag("shadow_item")
    inst:AddTag("wanda_alarm_weapon")

    inst.AnimState:SetBank("pocketwatch_weapon")
    inst.AnimState:SetBuild("pocketwatch_weapon")
    inst.AnimState:PlayAnimation("idle", true)

    MakeInventoryFloatable(inst, "small", 0.05, { 1.2, 0.75, 1.2 })

    inst.entity:SetPristine()

    if not TheWorld.ismastersim then
        return inst
    end

    inst:AddComponent("inventoryitem")
    inst.components.inventoryitem.imagename = "pocketwatch_weapon"
    inst.components.inventoryitem.atlasname = "images/inventoryimages.xml"

    inst:AddComponent("inspectable")
    inst:AddComponent("lootdropper")

    inst:AddComponent("equippable")
    inst.components.equippable:SetOnEquip(onequip)
    inst.components.equippable:SetOnUnequip(onunequip)
    inst.components.equippable.restrictedtag = "pocketwatchcaster"

    inst:AddComponent("weapon")
    inst.components.weapon:SetDamage(TUNING.POCKETWATCH_SHADOW_DAMAGE * 1.2)
    inst.components.weapon:SetRange(TUNING.WHIP_RANGE)
    inst.components.weapon:SetOnAttack(onattack)

    inst:AddComponent("fueled")
    inst.components.fueled.fueltype = FUELTYPE.NIGHTMARE
    inst.components.fueled:InitializeFuelLevel(4 * TUNING.LARGE_FUEL)
    inst.components.fueled.accepting = true

    MakeHauntableLaunch(inst)

    return inst
end

return Prefab("desperate_pocketwatch_weapon", fn, assets, prefabs)
