require "TienDualwield_Core"

TienDualwield.Keys = {}

local Keys = TienDualwield.Keys

Keys.SECTION = "[Dual Wield]"
Keys.SWAP = "TDW Swap Hands"
Keys.OFFHAND = "TDW Off Hand"
Keys.BOTH = "TDW Both Hands"

local function addKeyBindings()
    for _, bind in ipairs(keyBinding) do
        if bind.value == Keys.SECTION then
            return
        end
    end
    table.insert(keyBinding, { value = Keys.SECTION })
    table.insert(keyBinding, { value = Keys.SWAP, key = 0 })
    table.insert(keyBinding, { value = Keys.OFFHAND, key = 0 })
    table.insert(keyBinding, { value = Keys.BOTH, key = 0 })
end

if keyBinding then
    addKeyBindings()
end

function Keys.IsOffhandHeld()
    local key = getCore():getKey(Keys.OFFHAND)
    return key ~= nil and key ~= 0 and isKeyDown(key)
end

local function onKeyPressed(key)
    if not key or key == 0 then
        return
    end
    local player = getSpecificPlayer(0)
    if not player or player:isDead() then
        return
    end
    if getCore():isKey(Keys.SWAP, key) then
        TienDualwield.Client.SwapHands(player)
    elseif getCore():isKey(Keys.BOTH, key) then
        TienDualwield.Client.BothAttack(player)
    end
end

Events.OnKeyPressed.Add(onKeyPressed)
