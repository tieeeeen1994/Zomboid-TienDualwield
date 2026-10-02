require "TienDualwield_Core"

TienDualwield.Client = {}

local Client = TienDualwield.Client

local function say(player, key)
    HaloTextHelper.addBadText(player, getText(key))
end

function Client.SwapHands(player)
    if not TienDualwield.IsSwapHandsOn() then
        return
    end
    local primary = player:getPrimaryHandItem()
    local secondary = player:getSecondaryHandItem()
    if primary == secondary or (not primary and not secondary) then
        say(player, "IGUI_TienDualwield_NothingToSwap")
        return
    end
end

function Client.BothAttack(player)
    if not TienDualwield.IsBothAttackOn() then
        return
    end
    local pair = TienDualwield.GetPair(player)
    if not pair or pair.pair == TienDualwield.PAIR_MIXED then
        say(player, "IGUI_TienDualwield_NeedTwoWeapons")
        return
    end
end
