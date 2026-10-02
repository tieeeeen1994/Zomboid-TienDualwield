TienDualwield = TienDualwield or {}

local Mod = TienDualwield

Mod.MODULE = "TienDualwield"

Mod.KIND_MELEE = "melee"
Mod.KIND_HANDGUN = "handgun"

Mod.PAIR_MELEE = "melee"
Mod.PAIR_MIXED = "mixed"
Mod.PAIR_HANDGUNS = "handguns"

local function option(name)
    local vars = SandboxVars and SandboxVars.TienDualwield
    if not vars or vars[name] == nil then
        return true
    end
    return vars[name] == true
end

function Mod.IsSwapHandsOn()
    return option("SwapHands")
end

function Mod.IsOffhandAttackOn()
    return option("OffhandAttack")
end

function Mod.IsBothAttackOn()
    return option("BothAttack")
end

function Mod.IsDualHandgunsOn()
    return option("DualHandguns")
end

function Mod.WeaponKind(item)
    if not item or not instanceof(item, "HandWeapon") then
        return nil
    end
    if item:isTwoHandWeapon() then
        return nil
    end
    local swing = item:getSwingAnim()
    if swing == "Throw" or swing == "Heavy" then
        return nil
    end
    if item:isRanged() then
        return Mod.KIND_HANDGUN
    end
    return Mod.KIND_MELEE
end

function Mod.GetPair(player)
    if not player then
        return nil
    end
    local primary = player:getPrimaryHandItem()
    local secondary = player:getSecondaryHandItem()
    if not primary or not secondary or primary == secondary then
        return nil
    end
    local a = Mod.WeaponKind(primary)
    local b = Mod.WeaponKind(secondary)
    if not a or not b then
        return nil
    end
    local pair = Mod.PAIR_MIXED
    if a == Mod.KIND_MELEE and b == Mod.KIND_MELEE then
        pair = Mod.PAIR_MELEE
    elseif a == Mod.KIND_HANDGUN and b == Mod.KIND_HANDGUN then
        pair = Mod.PAIR_HANDGUNS
    end
    return { primary = primary, secondary = secondary, pair = pair }
end
