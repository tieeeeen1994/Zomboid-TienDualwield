if isClient() then return end

require "TienDualwield_Core"

TienDualwield.Server = {}

local Server = TienDualwield.Server

local Commands = {}

local function onClientCommand(module, command, player, args)
    if module ~= TienDualwield.MODULE then
        return
    end
    local handler = Commands[command]
    if handler then
        handler(player, args or {})
    end
end

Server.Commands = Commands

Events.OnClientCommand.Add(onClientCommand)
