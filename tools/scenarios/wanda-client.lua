return function(t)
    t.Assert("wanda_client_character", ThePlayer.prefab == "wanda", ThePlayer.prefab)
    local badge = ThePlayer.HUD.controls.status.heart
    t.Assert("wanda_age_badge_present", badge ~= nil and badge.year_hand ~= nil)
    t.Done("旺达真实客户端基础对象与网络同步检查完成")
end
