return function(api)
    local function assert_test(name, ok, details)
        api.assert(name, ok == true, details)
    end

    local function has_ingredient(recipe, ingredient)
        if recipe == nil or recipe.ingredients == nil then
            return false
        end
        for _, item in ipairs(recipe.ingredients) do
            if item.type == ingredient then
                return true
            end
        end
        return false
    end

    local timebox_recipe = AllRecipes ~= nil and AllRecipes.wanda_timebox_1 or nil
    assert_test("timebox_1_recipe_exists", timebox_recipe ~= nil)
    assert_test("timebox_1_uses_vanilla_time_shard", has_ingredient(timebox_recipe, "pocketwatch_parts"))
    assert_test("timebox_1_no_custom_time_shard", not has_ingredient(timebox_recipe, "wanda_time_shard"))
    assert_test("timebox_1_no_builder_skill", timebox_recipe ~= nil and timebox_recipe.builder_skill == nil)
    assert_test("timebox_1_clockmaker_only", timebox_recipe ~= nil and timebox_recipe.builder_tag == "clockmaker")
    assert_test("timebox_1_science_machine", timebox_recipe ~= nil and timebox_recipe.level ~= nil and timebox_recipe.level.SCIENCE == 1)
    assert_test("custom_time_shard_recipe_removed", AllRecipes == nil or AllRecipes.wanda_time_shard == nil)
    assert_test("timebox_equip_slot_registered", EQUIPSLOTS ~= nil and EQUIPSLOTS.WANDA_TIMEBOX == TUNING.WANDA_SKILLTREE_MOD.TIMEBOX_SLOT)

    local box = api.spawn("wanda_timebox_1")
    assert_test(
        "timebox_1_equips_custom_slot",
        box ~= nil and box.components ~= nil and box.components.equippable ~= nil and box.components.equippable.equipslot == EQUIPSLOTS.WANDA_TIMEBOX
    )
    api.remove(box)

    assert_test("rename_action_registered", ACTIONS ~= nil and ACTIONS.WANDA_RENAME_WATCH ~= nil)
    assert_test("rename_action_right_click", ACTIONS ~= nil and ACTIONS.WANDA_RENAME_WATCH ~= nil and ACTIONS.WANDA_RENAME_WATCH.rmb == true)

    local pencil = api.spawn("featherpencil")
    assert_test("featherpencil_has_drawingtool", pencil ~= nil and pencil.components ~= nil and pencil.components.drawingtool ~= nil)
    assert_test("featherpencil_tagged_for_watch_rename", pencil ~= nil and pencil:HasTag("wanda_watch_renamer"))
    api.remove(pencil)

    local recall = api.spawn("pocketwatch_recall")
    local portal = api.spawn("pocketwatch_portal")
    assert_test("recall_watch_has_writeable", recall ~= nil and recall.components ~= nil and recall.components.writeable ~= nil)
    assert_test("portal_watch_has_writeable", portal ~= nil and portal.components ~= nil and portal.components.writeable ~= nil)
    assert_test(
        "recall_watch_not_default_writeable",
        recall ~= nil and recall.components ~= nil and recall.components.writeable ~= nil and recall.components.writeable.writeable_by_default == false
    )
    assert_test(
        "portal_watch_not_default_writeable",
        portal ~= nil and portal.components ~= nil and portal.components.writeable ~= nil and portal.components.writeable.writeable_by_default == false
    )
    api.remove(recall)
    api.remove(portal)

    local wanda_ok, wanda = pcall(SpawnPrefab, "wanda")
    assert_test("spawn_wanda_for_skill_checks", wanda_ok and wanda ~= nil, tostring(wanda))
    if wanda_ok and wanda ~= nil then
        local starting_age = TUNING.WANDA_MAX_YEARS_OLD - wanda.components.health.currenthealth
        wanda.components.skilltreeupdater.IsActivated = function(_, skill)
            return skill == "wanda_age_max_1"
        end
        if wanda.ApplyWandaSkillTreeBonuses ~= nil then
            wanda:ApplyWandaSkillTreeBonuses()
        end
        assert_test("age_max_1_internal_span", wanda.components.health.maxhealth == 80, tostring(wanda.components.health.maxhealth))
        assert_test(
            "age_max_1_preserves_current_age",
            (100 - wanda.components.health.currenthealth) == starting_age,
            tostring(100 - wanda.components.health.currenthealth) .. " vs " .. tostring(starting_age)
        )
        assert_test(
            "age_max_1_syncs_classified_max",
            wanda.player_classified ~= nil and wanda.player_classified.maxhealth:value() == 80,
            wanda.player_classified ~= nil and tostring(wanda.player_classified.maxhealth:value()) or "nil classified"
        )

        wanda.age_state = "old"
        if wanda.components ~= nil and wanda.components.skilltreeupdater ~= nil then
            wanda.components.skilltreeupdater.IsActivated = function(_, skill)
                return skill == "wanda_old_calm"
            end
        end
        if wanda.ApplyWandaSkillTreeBonuses ~= nil then
            wanda:ApplyWandaSkillTreeBonuses()
        end

        assert_test("old_calm_adds_mighty_tag", wanda:HasTag("mightiness_mighty"))
        assert_test("old_calm_removes_slowbuilder", not wanda:HasTag("slowbuilder"))
        assert_test("old_calm_allows_heavy_lifting", wanda.components ~= nil and wanda.components.inventory ~= nil and wanda.components.inventory.noheavylifting == false)
        assert_test(
            "old_calm_hammer_mighty_mult",
            wanda.components ~= nil
                and wanda.components.workmultiplier ~= nil
                and wanda.components.workmultiplier:GetMultiplier(ACTIONS.HAMMER) == TUNING.MIGHTY_WORK_EFFECTIVENESS
        )
        assert_test(
            "old_calm_efficientuser_mighty_mult",
            wanda.components ~= nil
                and wanda.components.efficientuser ~= nil
                and wanda.components.efficientuser:GetMultiplier(ACTIONS.HAMMER) == TUNING.MIGHTY_WORK_EFFECTIVENESS
        )
        assert_test(
            "old_calm_sailing_mighty_mult",
            wanda.components ~= nil
                and wanda.components.expertsailor ~= nil
                and wanda.components.expertsailor:GetRowForceMultiplier() == TUNING.MIGHTY_ROWER_MULT
        )

        local heal = api.spawn("pocketwatch_heal")
        if heal ~= nil and heal.components ~= nil and heal.components.pocketwatch ~= nil then
            wanda.components.skilltreeupdater.IsActivated = function(_, skill)
                return skill == "wanda_heal_bonus_2"
            end
            wanda.components.oldager:StopDamageOverTime()
            local success = heal.components.pocketwatch:CastSpell(wanda)
            assert_test("heal_bonus_cast_success", success == true, tostring(success))
            assert_test("heal_bonus_uses_age_units", wanda.components.oldager.damage_remaining == -13, tostring(wanda.components.oldager.damage_remaining))
            api.remove(heal)
            api.remove(wanda)
        else
            assert_test("pocketwatch_heal_spawned_for_bonus_check", false)
            api.remove(heal)
            api.remove(wanda)
        end
    end
end
