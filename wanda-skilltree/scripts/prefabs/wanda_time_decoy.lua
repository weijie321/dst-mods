local assets =
{
    Asset("ANIM", "anim/player_basic.zip"),
}

local function Explode(inst)
    if inst._exploded then
        return
    end
    inst._exploded = true

    if inst.components.combat ~= nil then
        local x, y, z = inst.Transform:GetWorldPosition()
        local ents = TheSim:FindEntities(x, y, z, 3, { "_combat" }, { "INLIMBO", "playerghost", "FX" })
        for _, ent in ipairs(ents) do
            if ent ~= inst and ent.components.health ~= nil and not ent.components.health:IsDead() then
                ent.components.combat:GetAttacked(inst, TUNING.WANDA_SKILLTREE_MOD.DECOY_DAMAGE)
            end
        end
    end

    local fx = SpawnPrefab("explode_small")
    if fx ~= nil then
        fx.Transform:SetPosition(inst.Transform:GetWorldPosition())
    end
    inst:Remove()
end

local function OnAttacked(inst)
    Explode(inst)
end

local function fn()
    local inst = CreateEntity()

    inst.entity:AddTransform()
    inst.entity:AddAnimState()
    inst.entity:AddNetwork()

    MakeCharacterPhysics(inst, 10, .5)

    inst.AnimState:SetBank("wilson")
    inst.AnimState:SetBuild("wilson")
    inst.AnimState:PlayAnimation("idle_loop", true)
    inst.AnimState:SetMultColour(0.4, 0.25, 0.8, 0.55)

    inst:AddTag("character")
    inst:AddTag("scarytoprey")
    inst:AddTag("notraptrigger")
    inst:AddTag("NOBLOCK")

    inst.entity:SetPristine()

    if not TheWorld.ismastersim then
        return inst
    end

    inst.persists = false

    inst:AddComponent("health")
    inst.components.health:SetMaxHealth(1)

    inst:AddComponent("combat")

    inst:ListenForEvent("attacked", OnAttacked)
    inst:DoTaskInTime(3, Explode)

    return inst
end

return Prefab("wanda_time_decoy", fn, assets)
