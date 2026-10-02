# Tien's Dual Wield

Project Zomboid B42 mod: fight with a one-handed weapon in each hand. It recreates what Brutal Handwork did (that mod is
discontinued and desyncs in multiplayer), and it is built for multiplayer from the start. The live code is under
`Contents/mods/TienDualwield/42/`.

The Lua source has no comments on purpose. Non-obvious reasoning lives here; update this file when it changes.

Related notes elsewhere (read them, don't repeat them here):
- `~/Zomboid/Workshop/ZomboidFixesB42/CLAUDE.md`: general engine notes. See "Hands, hand models and attacks" (primary =
  right hand, attacks use only the primary, hand model selection), the networking sections, key bindings (vanilla
  `keyBinding` table, not ModOptions, because ModOptions drops Shift/Ctrl/Alt) and how to decompile the game.
- `~/Zomboid/Workshop/TienInspectWeapon/CLAUDE.md`: everything about animations. It covers the `.x` clip pipeline
  (`scripts/anim/xanim.py`, Blender import/export), the rig, how anim nodes are picked, prop bone reparenting, and the
  fact that the engine has no animation mirroring.

## Status

- **2026-10-02:** skeleton created. Nothing works in game yet. It has passed only a luaparser syntax check and JSON
  validation.
- **Design:** under discussion with the user (see "Open questions").
- **Research:**
  - Done and recorded below: multiplayer combat networking, the melee pipeline and the firearm pipeline.
  - **Not recorded: the input / equipping / animation-set inventory.** It was still running when the session stopped
    (2026-10-02), so redo it. Questions to cover:
    - attack input and the default keys (Aim / Attack / Shove);
    - `ISEquipWeaponAction` paths and the cleanest hand swap;
    - left-hand hold masks (`LeftHandMask`, see firearms below);
    - adding anim nodes gated on a custom variable;
    - anim events reaching Lua;
    - vanilla left-hand clips;
    - joypad buttons.
- **Decompile:** the 42.20 decompile used for this lives in a session scratchpad, so it is temporary. Re-create it with
  the Vineflower recipe in ZomboidFixesB42/CLAUDE.md. Line numbers below are from that decompile (`zombie/...`).

## What the user asked for (2026-10-02)

1. **Swap hands:** a keybind swaps the items in the two hands.
2. **Off-hand swing:** the secondary (left) hand can swing.
3. **Both melee weapons can swing.**
4. **Modifier + attack:** with two one-handed weapons (or a one-handed gun), modifier + attack uses the off-hand weapon.
5. **Both at once:** another keybind swings both weapons together, like a power attack.
6. **Two pistols always shoot together.** The off-hand gun can never fire on its own.
7. **Reload is primary only.** Reload always means the primary weapon; swap hands to reload the other one.
8. The user asked "what else am I missing?" (see "Open questions").

## Brutal Handwork (the mod being replaced), what is known

Source: aqxaromods mirror of the Workshop page (Steam returned 429). Workshop id 2934621024, B41 era.
- **Requires Fancy Handwork.** Fancy Handwork fixed the weapon-holding animations, added a modifier key, and synced
  animation state locally and over MP.
- **Off-hand attacks:**
  - With only a secondary weapon equipped, the player attacks with the off hand automatically.
  - With both hands armed, modifier while aiming attacks with the off hand.
  - A sandbox option alternates main and off-hand attacks automatically.
- **Stats:** off-hand attack speed and damage are "mostly vanilla" (skills, injuries). Off-hand swings hit the
  environment (windows break).
- **Unarmed:** hold the modifier while aiming to raise fists. Fists do small damage, scaled by Strength and Fitness.
  Sandbox options exist for always raising fists and for disabling unarmed.
- **Modifier key:** Left Ctrl on keyboard, Left Bumper on a controller. The author told players to rebind the vanilla Aim
  key, which is also Left Ctrl.
- **Compatibility:** "Calls ALL relevant Events during an attack, for compatibility with mods." Dual handguns were only
  planned, never released.

## Files (skeleton)

- **`shared/TienDualwield_Core.lua`:** the `TienDualwield` table and `MODULE`.
  - Sandbox getters `Is*On()`; a missing option reads as on.
  - `WeaponKind(item)`: `melee` or `handgun` for a one-handed HandWeapon. Two-handed, `Throw` and `Heavy` swing anims
    give nil.
  - `GetPair(player)`: `{ primary, secondary, pair = melee | mixed | handguns }`, or nil unless each hand holds a
    different one-handed weapon.
- **`client/TienDualwield_Keys.lua`:** the vanilla key-binding section `[Dual Wield]` with three binds:
  - `TDW Swap Hands`, `TDW Off Hand` (a held modifier: `Keys.IsOffhandHeld()` polls `isKeyDown`), `TDW Both Hands`.
  - All three default to unbound, which avoids the Left Ctrl / Aim clash Brutal Handwork had.
  - `OnKeyPressed` dispatches to `Client.SwapHands` / `Client.BothAttack`.
- **`client/TienDualwield_Client.lua`:** `SwapHands` and `BothAttack` stubs. So far they only check the option and show
  the "nothing to swap" / "needs two weapons" halo text.
- **`server/TienDualwield_Server.lua`:** an `OnClientCommand` dispatcher (`Server.Commands[command](player, args)`) with
  no commands yet.
- **Sandbox options** (`sandbox-options.txt`, page `TienDualwield`): one per feature, all on by default: `SwapHands`,
  `OffhandAttack`, `BothAttack`, `DualHandguns`. The penalty and tuning options wait for the design.
- **Translations:** `Translate/EN/Sandbox.json`, `UI.json` (key binding labels), `IG_UI.json`.
- **Not created yet:**
  - `poster.png` / `icon.png` / `preview.png` (mod.info has no poster/icon lines until they exist).
  - `media/AnimSets/player/...` and `media/anims_X/Bob/` (mirrored clips).
  - `scripts/` (the clip mirroring tool, art script).
  - workshop.txt has no `id` yet (it gets one on first upload) and is `visibility=private`.

## Engine findings: who decides a hit in multiplayer (42.20)

### The hit is decided on the attacking client

- **Detection:** only the attacking client detects hits. `SwipeStatePlayer.java:279-296` runs the `AttackCollisionCheck`
  anim event only for `IsoPlayer.isLocalPlayer(owner)`, once per swing (the `ATTACKED` param).
- **Weapon:** `CombatManager.getWeapon(owner)` = `getAttackingWeapon()` = `useHandWeapon` (`IsoLivingCharacter.java:182-193`).
  `useHandWeapon` is set from the primary item only (`SwipeStatePlayer.java:128-134`, `IsoGameCharacter` `setPrimaryHandItem`
  ~3357).
- **`CombatManager.attackCollisionCheck` (651-1245), in order:**
  1. Fires `OnWeaponSwingHitPoint` (670).
  2. Sends `AttackCollisionCheckPacket` (weapon ID and hit count, 708-711).
  3. Computes every hit's damage locally (959-1103: random damage, damage mod, pain, moodles, crits).
  4. Applies the damage to its own copy of the target with `Hit(...)` (1154).
  5. Sends one packet per target through `GameClient.sendPlayerHit` (1238-1244; `GameClient.java:1223-1248`).
- **Packet per target:**

  | Target | Packet |
  |---|---|
  | nothing (sent on a miss too, 1226) | `PlayerHitSquare` |
  | animal | `PlayerHitAnimal` |
  | player | `PlayerHitPlayer` |
  | zombie | `PlayerHitZombie` |
  | vehicle (client sums the damage) | `PlayerHitVehicle` |
  | object / tree / thumpable | `PlayerHitObject` |

- **Hit packet contents** (`packets/hit/PlayerHit.java:20-75`, `fields/hit/*`):
  - Wielder block: ID, position, direction, reactions, flags, `charge`, Aiming perk, `CombatSpeed`, `AttackType`, the
    full `AttackVars`, and the hit list.
  - Weapon: **item ID only** (`fields/hit/Weapon.java:20-23`), no hand flag.
  - Per hit: damage (clamped to 100 by the client), force, direction, range, body part.
  - All hit packets: reliability 3 (RELIABLE_ORDERED), channel 0, capability `LoginOnServer`.

### What the server does with a hit packet

- **Order:** `parseServer` → `isConsistent` → anticheats → `processServer` (`PacketTypes.java:736-771`). A failure drops
  the packet: it is not applied and not relayed.
- **`isConsistent`** only checks that the wielder, weapon and target exist. Nothing checks that the wielder is the
  sender's own player.
- **Damage is not recomputed.** `WeaponHit.process` (`WeaponHit.java:77-130`) calls `target.Hit(weapon, wielder, damage,
  ignoreDamage, range, true)`. With `bRemote` true, `IsoGameCharacter.Hit` takes the client's number (6103).
- **Done by the server itself:**
  - Aggro, blood.
  - Combat XP through server Lua `OnWeaponHitXp` (`server/XpSystem/XpUpdate.lua:50-90`, by the packet's weapon).
  - Melee condition loss and Maintenance XP (`processMaintenanceCheck`, see below).
  - Endurance (`AttackCollisionCheckPacket` 76-82, for the packet's weapon, no anticheat).
  - Death (`die()` → `ZombieDeath` broadcast).
- **Objects:** `IsoObject.WeaponHit(player, weapon)` runs `hitCount` times and the server computes the damage itself
  (`PlayerHitObjectPacket.java:69-87`).
- **Vehicles:** `vehicle.processHit(wielder, weapon, clientDamage)` trusts the client.
- **Relay:** `GameServer.sendHitCharacter` (`GameServer.java:3140-3150`) relays to every relevant connection except the
  sender.

### The off-hand trap (why Brutal Handwork desynced)

- **The server accepts any HandWeapon in the attacker's top-level inventory, by ID** (`fields/hit/Weapon.java:30-33`,
  `getItemWithID`, not recursive). It never checks the hand.
- **Other clients accept only the attacker's primary item.** If the primary is empty they use `bareHands`, and if the ID
  does not match they drop the packet silently (`Weapon.java:34-41`; `PacketTypes.java:787-791` only reports it):
  ```java
  if (character.getPrimaryHandItem() != null) {
     if (character.getPrimaryHandItem().getID() == this.getID()) weapon = primary;   // else stays null -> dropped
  } else weapon = character.bareHands;
  ```
- **A secondary-weapon hit therefore lands on the server only.** Remote clients show no swing, reaction or blood, and
  their copy takes no damage.
- **The zombie's owner client then reverts it.** The owner sends zombie health in `ZombiePacket` (`NetworkZombieAI.java:169`)
  and the server takes it unconditionally (`popman/NetworkZombiePacker.java:65-82`, 225-243 `setHealth`). The owner is
  the grappler, else the targeted player, else the closest player (`NetworkZombieManager.java:58-125`). If the owner is
  not the attacker and dropped the hit, its next update writes the old health back over the server's.
- **Lethal hits survive**, because death goes through the server's `die()`.
- **Rule for this mod:** every hit packet's weapon ID must equal the attacker's primary-hand item as **other clients**
  see it.
- **Melee condition loss** happens on the server (`processMaintenanceCheck`, `CombatManager.java:518-556`, only when
  `!GameClient.client`):
  - It needs `isActuallyAttackingWithMeleeWeapon()` (`IsoGameCharacter.java:16668-16685`): the server's **primary** must
    be a melee HandWeapon, `useHandWeapon` set, not bare hands, not shoving.
  - It then damages the **packet's** weapon (529/534), and `checkSyncItemFields` sends `SyncItemFields` to the owner.
- **Firearms:**
  - Condition loss is client side (`CombatManager.java:1216-1219` `damageCheck` → `syncItemFields`).
  - The server takes ammo in Lua: `ISReloadWeaponAction.onShoot`, `shared/TimedActions/ISReloadWeaponAction.lua`
    ~510-527 (registered at 542), runs only when `not isClient()`, then calls `syncHandWeaponFields`.
  - `ammoBeforeShot` is recorded on the first hit of each shot (`fields/hit/Player.java:154-173`).
- **Client item syncs are not validated.** The server accepts client `SyncItemFields` / `SyncHandWeaponFields` without
  checks (`SyncItemFieldsPacket.java:513-521`, `SyncHandWeaponFieldsPacket.java:241-250`).

### Combat anticheats (`anticheats/AntiCheat.java:21-43`)

- **Setting:** server option `AntiCheatHit`, default 2 = Kick (1 Ban, 2 Kick, 3 Log, 4 Disabled; `ServerOptions.java:184-199`).
- **On a failure:**
  - The packet is dropped and the player's counter goes up.
  - At `maxSuspiciousCounter` the player is kicked or banned. `Core.debug` and the `CantBeKickedByAnticheat` capability
    skip that.
  - Counters drop by 1 every 150 s (`SuspiciousActivity.java:10-30`).
- **The checks:**

  | Anticheat | Strikes | Check |
  |---|---|---|
  | HitDamage | 1 | each hit's damage ≤ 100 |
  | HitLongDistance | 2 | target distance ≤ `relevantRange*8*1.2` |
  | HitShortDistance | 2 | distance ≤ 10 (zombie and vehicle hits only) |
  | HitWeapon | 2 | range, ammo and **rate** (below) |
  | Safety | 1 | PvP rules (god mode, PvP off, faction, safety, non-PvP zones) |

- **HitWeapon, in order:**
  1. Range: `max(0, dist - 5) <= weapon.getMaxRange()` (the packet's weapon).
  2. Ammo, for aimed firearms: `ammoBeforeShot` or current + chambered > 0.
  3. Rate (`AttackRateChecker.java:14-24`): timestamps over a `3×T` window, `hitCount` entries per packet; it fails above
     `maxHits*3`.
     - T = 400 ms melee, 150 ms single shot, 15 ms automatic.
     - `maxHits = projectileCount*maxHitCount`, at least 3 when the sandbox MultiHitZombies option is on.
     - So a melee weapon with `maxHitCount=1` and multi-hit off allows **3 hits per 1.2 s per player across all
       weapons**.
     - The checker is per player (`NetworkCharacterAI.java:58`), so extra off-hand or double-swing hits eat the same
       budget. **Two violations = kick by default.**
- **Which packets get which checks:**
  - PlayerHitZombie and PlayerHitAnimal: HitDamage, HitLongDistance, HitWeapon.
  - PlayerHitPlayer: the same plus Safety.
  - PlayerHitObject: HitLongDistance, HitWeapon.
  - PlayerHitSquare and PlayerHitVehicle: HitLongDistance only.

### How other clients show a remote attack

- **The swing starts when the hit packet arrives.** Other clients start the swing animation from it: `Player.attack()`
  (`fields/hit/Player.java:133-147`) sets `useHandWeapon`, copies `AttackVars` and the hit list, and calls
  `pressedAttack()`. A miss still sends `PlayerHitSquare`, so remote swings always play.
- **Per-attack anim data rides in the hit packet:** `recoilVarX`, `AttackType`, `CombatSpeed`, `AimFloorAnim`, shove,
  grapple, from-behind, crit, hit reactions (`Player.java:117-131`).
- **PlayerUpdate** (`PlayerPacket`) carries only position, a 16-bit flag set (`NetworkPlayerVariables.java:17-35`:
  sneaking, running, aiming `isCharging`, doShove, performingAction...) and walk/idle speeds.
- **`Weapon` (anim variable)** is recomputed on every machine from its own copy of the hands
  (`IsoGameCharacter.java:3375`, 3741). Remote hands come from `EquipPacket`.
- **`SwipeStatePlayer` is `syncOnEnter`:** a `StatePacket` is relayed, and the server never runs the swing state.
- **Custom anim variables are not synced** unless the owning client calls `addVariableToSyncList("X")`
  (`LuaManager.java:8991-8996`). After that:
  - Each `setVariable` sends `VariableSync`, which the server stores and relays (`VariableSyncPacket.java:86-111`).
  - **Every** synced key of every player is re-sent with **every** PlayerUpdate relay to every viewer
    (`GameServer.setCustomVariables` 2763-2769, called at `PlayerPacket.java:200`). That is heavy, so keep synced
    variables to one or two.
  - Only String, Boolean and Float values work; `setVariableEnum` breaks it.

### EquipPacket (`packets/EquipPacket.java`): what a hand swap costs

- **Client → server:** 2 item IDs, sent by `IsoGameCharacter.updateHandEquips()` (8704-8711, callable from Lua). A
  plain client `setPrimaryHandItem` only marks a flag; Lua `sendEquip` is server only (`LuaManager.java:4308-4316`).
- **On the server:** no validation beyond `getItemWithID` in the top-level inventory (a missing ID empties the hand), no
  rate limit. It sets the hands (`OnEquipPrimary/Secondary`, models, `Weapon` variable) and relays to **all** clients,
  not range limited.
- **On remote clients:** the packet is a full `saveWithSize` of each hand item, and they load a **new item copy** each
  time.
- **Echo:** setters run on the server send Equip to the owner, who sends its IDs back, which the server relays again
  (`IsoGameCharacter.java:8671-8675`, `EquipPacket.java:166-173`).
- **One client swap costs** about 1 small packet up, 1 full-item packet to the owner and 2 full-item relays to every
  client. All are on channel 0, ordered with the hit packets.
- **A per-attack swap is visible:** models jump and OnEquip events and the `Weapon` type change on every client. Vanilla
  equips go through `ISEquipWeaponAction:complete()` on the server (`shared/TimedActions/ISEquipWeaponAction.lua:138-200`).
- **A swap keybind at the user's pace is fine.** It is just a quick equip, ideally a short server-run timed action like
  vanilla's.

### Hooks that fire on the server for a hit

| Hook | Notes |
|---|---|
| `OnHitZombie(zombie, wielder, bodyPart, weapon)` | `IsoZombie.java:1355` |
| `OnWeaponHitCharacter(wielder, target, weapon, damage)` | `IsoGameCharacter.java:6084` |
| `OnPlayerGetDamage` | |
| Hook `WeaponHitCharacter` | returning true cancels the damage on the server (6086, `LuaHookManager.java:127`) |
| `OnWeaponHitXp`, `OnWeaponHitTree`, `OnWeaponHitThumpable`, `OnZombieDead` | |
| `OnWeaponSwingHitPoint` | firearms, once per shot |

- `OnWeaponSwing`, Hook `WeaponSwing` and `OnPlayerAttackFinished` fire only on clients.
- **No Lua function applies and replicates a weapon hit.**
  - `sendHitZombie` / `sendHitPlayer` are deprecated client helpers (`LuaManager.java:3211-3270`), and `sendHitPlayer`
    always uses the primary.
  - `CombatManager`, `GameClient` and `WeaponHit` are not exposed (only `CombatConfig`, `LuaManager.java:1840`).
- **Hitting from server Lua** (`zombie:Hit(weapon, player, dmg, false, 1, true)`) replicates only when it kills.
  Non-lethal damage is overwritten by the owner client's next `ZombiePacket`.
- **Client lever:** `player:setUseHandWeapon(item)` before the `AttackCollisionCheck` event makes the whole vanilla
  swing use that item (damage, packets, range check). Remote clients still drop the packets unless that item is their
  copy's primary.

## Engine findings: the melee swing (42.20)

### Input to swing

- **Input:** `IsoPlayer` 2503-2560 (also 4478-4492).
  - The shove key sets `setDoShove(true)`, then `AttemptAttack`.
  - Aim + attack calls `AttemptAttack` when `CanAttack()` passes, `getRecoilDelay() <= 0` and `getMeleeDelay() <= 0`.
- **`CanAttack`** (`IsoGameCharacter` 6381-6425): false while `isPerformingAttackAnimation()`. Otherwise it **resets
  `useHandWeapon` to the primary**, and unequips a primary with condition <= 0.
- **`IsoLivingCharacter.AttemptAttack`** (36-54): only when the primary is a HandWeapon. It runs `calculateAttackVars`,
  then `Hook.Attack(character, chargeDelta, primary)`.
  - Any registered `Hook.Attack` callback suppresses Java's own `DoAttack`.
  - Vanilla `ISReloadWeaponAction.attackHook` (`shared/TimedActions/ISReloadWeaponAction.lua` 427-467) calls
    `DoAttack` itself. To change attacks, `Remove` it and wrap it.
- **`DoAttack` → `CombatManager.pressedAttack`** (3140-3352):
  - attack type from `WeaponType(primary)`;
  - `setCombatSpeed(calculateCombatSpeed())`;
  - `calculateAttackVars`, then `setUseHandWeapon(attackVars.getWeapon)`;
  - hit list, crit roll, attack-from-behind, `TargetDist`.
- **The swing state:** `actiongroups/player/idle/to_melee.xml` (initiateAttack, not rangedWeapon, not bDoShove) enters
  `SwipeStatePlayer`.
- **`AttackVars`** (`zombie/network/fields/hit/AttackVars.java`, not exposed to Lua) **holds no weapon.**
  - `getWeapon(owner)` returns `owner.getUseHandWeapon()` (or bareHands).
  - `calculateAttackVars` (`CombatManager` 1328-1432) uses the primary. **A non-HandWeapon primary forces doShove and
    bareHands whatever `useHandWeapon` is**, so a weapon in the off hand with an empty primary can never swing.
- **`SwipeStatePlayer.enter`** (156-240), in order:
  1. `calculateAttackVars`.
  2. `doAttack`: `useHandWeapon` = primary or bareHands (128-134).
  3. `OnWeaponSwing(player, weapon)` (199). This fires on every machine, including for remote copies.
  4. `Hook.WeaponSwing` (200). Any registered callback aborts every swing.
  5. `weapon = getAttackVars().getWeapon(player)` (209).
- **Anim events** (77-96):
  - `AttackCollisionCheck` (279-296): local player only, and only while `ATTACKED` is false. `ATTACKED` is set at the end
    of the check (`CombatManager` 1237), and Lua cannot reset it, so **a second collision check in the same swing is
    ignored**.
  - `PlaySwingSound` (353-377), `SetMeleeDelay` (397), `AttackAnim` (259).
- **`exit`** (406-474):
  - Applies stomp foot damage.
  - `removeFromHands(weapon)` when its condition is <= 0 (456-459). This is the break path; `changeWeapon` is dead code.
  - `OnPlayerAttackFinished(owner, weapon)` (468).

### Damage, condition, XP, endurance (`CombatManager.attackCollisionCheck` 651-1245)

- **Hit list** (`calculateHitInfoList` 2290-2398, by `useHandWeapon`):
  - `MaxHitCount`; 3 for a shove with a weapon; 1 with multi-hit off or a ground target.
  - Range is `maxRange * rangeMod`; then line of sight and windows.
- **Damage, in order:**
  1. `Rand(min, max) * DamageMod * HittingMod (Strength)` (959).
  2. Two-hander held in one hand: minus min damage (958-966).
  3. **Arm pain summed over both arms** (Hand_L..UpperArm_R, 982-992): above 10 it divides the damage. It does not care
     which hand swings.
  4. Traits, then the multi-target split.
  5. `rangeDel` (1016).
  6. Panic and stress −0.1 per level.
  7. Endurance and tired moodles ×0.5..0.05 (1048-1090).
  8. Hit location (head ×3, legs ×0.05, clothing defense).
  9. `target:Hit(weapon, owner, damageSplit, ignore, rangeDel)` (1154).
- **Inside `IsoGameCharacter.Hit`** (6069-6110, `processHitDamage` 6144-6206):
  - Strength and endurance force; ×1.5 from behind.
  - Weapon level `0.3 + 0.1 * getWeaponLevel()`: **from the primary**.
  - Crit / floor multipliers; `applyOneHandedDamagePenalty`; global ×0.15.
  - Knockdown = `isCriticalHit()` (`IsoZombie.hitConsequences` 4214).
- **Condition and Maintenance XP:** `processMaintenanceCheck` (518-556), SP or server only.
  - Gated by `isActuallyAttackingWithMeleeWeapon()` (16668): the primary must be a melee HandWeapon.
  - Damages the passed weapon (`damageCheck`, `InventoryItem` 4520).
- **Skill XP:** `XpUpdate.onWeaponHitXp` (`server/XpSystem/XpUpdate.lua` 50-106), with the perk from **the event's weapon**
  categories. It fires in SP at 1163 and on the MP server in `WeaponHit` 126.
- **Endurance and strain:**
  - `processWeaponEndurance` (1260) per swing; `applyMeleeEnduranceLoss` (3850) per hit.
  - `addCombatMuscleStrain` (16293). In MP these run on the server, for the packet's weapon.
- **Swing speed:** `calculateCombatSpeed` (`IsoGameCharacter` 9621-9658) uses **the primary only**.
  - Starts at `0.8 * BaseSpeed`.
  - Endurance, heavy load, weapon level, Fitness; ×0.95 with a bag in the secondary.
  - **Right-arm injuries only** (`getArmsInjurySpeedModifier` 9662-9682).
  - Clamped 0.8..1.6. It becomes the `CombatSpeed` anim variable, is synced in the hit packet, and Lua can override it
    with `setCombatSpeed` after `pressedAttack`.
- **Melee delay:** one value per character, set by the `SetMeleeDelay` event (12 for 1H, 8 for knife), decaying by
  0.625 a tick.
- **A HandWeapon in the secondary hand has no melee effect in vanilla.** The exceptions:
  - spiked armour on shoves (3994-4012);
  - a bag in the secondary ×0.95 speed;
  - a firearm primary with anything in the secondary: recoil ×1.3 (`HandWeapon` 1297).

### What `setUseHandWeapon(secondary)` changes

- **Where to set it:** in `OnWeaponSwing`, guarded by `isLocalPlayer()`.
  - It fires after `doAttack` reset to the primary and before `weapon` is read at 209.
  - It sticks for the swing (`CanAttack` is guarded by the AttackAnim flag; a one-frame gap before that is untested).
  - Setting it in `OnWeaponSwingHitPoint` is too late and gives a mix. Setting it in `Hook.Attack` is undone by `enter`.
- **Follows the override:**
  - hit list (range, angle, MaxHitCount);
  - min/max damage, DamageMod, crit multiplier, stagger and pushback;
  - swing and hit sounds;
  - every hit event, and therefore skill XP (the secondary's perk);
  - condition loss and maintenance;
  - door / window / tree / vehicle hits;
  - endurance and strain;
  - the MP packet weapon ID;
  - break removal; `OnPlayerAttackFinished`.
- **Still the primary:**
  - the animation (`Weapon`, attackType, crit node);
  - CombatSpeed, crit chance and crit flag (so knockdown), attack-from-behind;
  - knife closeKill / knife-crit eligibility;
  - the weapon-level damage multiplier, maintenance skill and tree skill (`getWeaponLevel` 11118-11157 casts the primary);
  - jaw-stab removal (`applyKnifeDeathEffect` 4026 removes the primary);
  - aiming delay; NO_CRITICALS / FAKE_SPEAR tags;
  - the `isActuallyAttackingWithMeleeWeapon` gate;
  - other machines rerun `doAttack` with the primary.
- **MP:** remote clients still drop the hit packets, because the ID is not their copy's primary (see networking above).

### Melee pieces reachable from Lua

- **`target:Hit(weapon, attacker, damage, ignoreDamage, modDelta[, bRemote])`.**
  - Does: the hit events and hooks, stagger, `processHitDamage`, death, zombie reaction and knockdown.
  - Does **not**: the damage roll and its penalties, clothing / head ×3, sounds, blood splash, condition, XP, endurance,
    or **any network send**.
- **Blood:** `splatBlood`, `splatBloodFloorBig`, `addBlood`.
- **Condition:** `damageCheck` / `reduceCondition` + `syncItemFields`.
- **XP:** `addXp`, server or SP only.
- **Sounds:** `getEmitter():playSound(weapon:getZombieHitSound())`.
- **Objects:** `IsoObject:WeaponHit(owner, weapon)`.
- **Not exposed:** `AttackVars`, `HitInfo`, `State.Param` (`ATTACKED`), `CombatManager`. Exposed: `SwipeStatePlayer`,
  `WeaponType`, `getCombatConfig()`.
- **Reachable setters:** `setUseHandWeapon`, `setCriticalHit`, `setCombatSpeed`, `setAttackFromBehind`, `setDoShove`,
  `setMeleeDelay`, `DoAttack`, `pressedAttack`, `AttemptAttack`.

### Shove, stomp, knife crits

- **Shove:**
  - Chosen by the shove key, a non-HandWeapon primary, or a target inside minRange that is not a knife closeKill.
  - Weapon `bareHands`, no damage, up to 3 hits with a weapon in the primary; a crit is the knockdown.
- **Stomp:** shove + aimAtFloor. Damage from Strength and the shoe's StompPower; Foot_R damage.
- **Weapon floor attack:** `aimAtFloor` without a shove, damage ×max(5, crit multiplier).
- **Knife crit:** needs `WeaponType(primary)` = knife, a target inside minRange and at most 1 zombie chasing (1397). It is
  forced from behind on an unaware zombie (`pressedAttack` 3300-3318). Nodes `melee/1handed/KnifeCrit.xml` /
  `KnifeCritBehind.xml`.
- All of these decisions read the primary.

## Engine findings: firearms (42.20)

### The shot

- **Gate:** `IsoPlayer` 2546-2558: aiming, `CanAttack`, recoil delay <= 0, melee delay <= 0. Then `AttemptAttack` →
  `Hook.Attack`.
- **`ISReloadWeaponAction.attackHook`** (427-467) works on the primary only:
  - Clears the queue and checks `canShoot` (408-423: not Safe, not jammed, chambered or ammo > 0).
  - Plays `playRangedWeaponShootSound(SwingSound)` (networked, `RangedWeaponSoundPacket`).
  - Adds noise with `addWorldSoundUnlessInvisible(SoundRadius * FirearmNoiseMultiplier ...)`.
  - Then `DoAttack(0)`, or `setRangedWeaponEmpty(true)` when it can't shoot.
- **`pressedAttack`:**
  - Requires `isWeaponReady()` (16739: the primary model loaded with a `muzzle` attachment).
  - Recoil delay from `HandWeapon.getRecoilDelay` (1290): Aiming and Strength, **×1.3 when this gun is the primary and a
    different item is in the secondary**. Vanilla already has an off-hand penalty.
  - Sends `PlayerEmptyShot` if the primary has 0 ammo.
- **The fire state:** the `ranged` state comes from `rangedWeapon` + `Weapon=handgun` (from the primary). The node is
  `AnimSets/player/ranged/handgun/HandgunDefault.xml`, with `AttackCollisionCheck "Shot"` at 0.001.
- **`attackCollisionCheck` for an aimed firearm** (698-703):
  - `startMuzzleFlash`, `getBallisticsController().update()`, `fireWeapon` (tracer).
  - Hit roll `Rand(100) <= chance` (763); damage `Rand(min, max)`; piercing reduction (786-806).
  - Condition loss is **client side** (1216-1219).
  - Line 679 (`isOtherHandUse` → `getSecondaryHandItem().Use()`) is the only place a shot touches the secondary.
- **Ammo, chamber, jams:** Lua `ISReloadWeaponAction.onShoot` (470-527, on `OnWeaponSwingHitPoint`), on the item passed
  in, i.e. the attacking weapon.
  - It un-chambers and sets spent; ejects (`ShellFallSound`; there is no casing model anywhere).
  - Re-chambers; `setCurrentAmmoCount` **only when `not isClient()`**.
  - `checkJam` (`HandWeapon` 2143) when `JamGunChance > 0`.
  - `syncHandWeaponFields` (server only).
  - On the MP server it is fired once per new shot ID (`fields/hit/Player.java` 149-186).
- **Hit chance** (`calculateHitChanceData` 2633-2788): weapon HitChance + Aiming, distance against sight range, aim delay,
  movement (Nimble), Marksman, **pain over both arms** (2623), weather, light (`LowLightBonus`), moodles, headgear.
- **Target selection:** one ray from the muzzle or the reticle point (`calculateBallistics` 1587), `MaxHitCount`,
  piercing within 1°.

### Everything is bound to the primary

- **Ballistics controller:** one per character, client only. Muzzle position and direction come from
  `primaryHandModel`'s `muzzle` attachment (`BallisticsController.java` 74-144, 194-207).
- **`setPrimaryHandItem`** (3349-3380) resets `useHandWeapon`, the controller targets, the hand models and `Weapon`.
  `setSecondaryHandItem` touches none of them.
- **Muzzle flash** (`EffectsManager.startMuzzleFlash` 40-68):
  - The light goes on the character's tile. The flash model comes from `getPrimaryHandItem().getMuzzleFlashModelKey()`
    and is drawn only on `primaryHandModel`.
  - One effect per character, so two flashes are impossible.
- **Tracer:** `IsoBulletTracerEffects.createEffect` (91-143) starts at the controller's muzzle position.
- **Reticle and HUD:**
  - `updateReticle` (3468-3526) is the primary, and it saves and restores `useHandWeapon` every frame.
  - There is no vanilla ammo HUD, only the tooltip.
- **Reload and rack:**
  - `IsoPlayer.checkReloading` (3490-3500) passes the primary to `OnPressReloadButton` / `OnPressRackButton`.
  - `ISFirearmRadialMenu` reads the primary (238, 294, 459).
  - `ISReloadWeaponAction`, `ISInsertMagazine` and `ISEjectMagazine` `isValid` require the primary. This matches the
    user's "reload = primary".
- **Empty or jammed primary:** `HandgunEmpty.xml` plays the primary's click; no shot, no events, the secondary is
  untouched.
- **No Lua function fires a shot from a non-primary gun.**
  - `CombatManager`, `EffectsManager`, `IsoBulletTracerEffects`, `BallisticsController` and `ModelInstance` are not
    exposed, and `primaryHandModel` / `secondaryHandModel` are fields.
  - A second gun from Lua would mean rebuilding: ammo / chamber / jam on the secondary (server side in MP), sound, noise,
    hit roll and target, damage, condition and XP.
  - **Tracer and muzzle flash cannot be done** for a gun that is not the primary.
- **MP:** each shot is `AttackCollisionCheckPacket` + one `PlayerHit*` per target (or `PlayerHitSquare`), with the weapon
  ID, shot ID and tracers.
  - Remote clients draw the flash and tracer only for an accepted packet, i.e. one whose weapon is the primary.
  - Anticheat ammo check: `ammoBeforeShot` or current + chambered > 0. Rate is about 3 hits per 450 ms with multi-hit off.

### Animations

- **Aim:** `aim/aim_handgun.xml` (`Bob_IdleAimHandgun` + vertical blends). In the plain handgun aim pose the left hand
  supports the gun.
- **Fire:** `ranged/handgun/HandgunDefault.xml`; `HandgunEmpty.xml` (`RangedWeaponEmpty`).
- **Variables:** `Weapon`, `aim`, `rangedWeapon`, `FireMode`, `recoilVarX/Y`, `singleShootSpeed`, `ShotDone`.
- **Left-arm masks (useful for a left-hand weapon hold):**
  - `maskingleft` is a substate whose child tags include `ranged`, so it stays on while firing.
  - It is driven by the `LeftHandMask` variable, which comes from the **secondary** item's script `secondaryAnimMask` /
    `ReplaceInSecondHand` (`scripting/objects/Item.java` 1446-1468). `ModelManager` sets it when it builds the secondary
    model.
  - Example: `maskingleft/aimhandguntorchleft.xml` plays `Bob_IdleAimHgun_Torch` (Weapon=handgun, aim, not moving).
    Bone weights from `holdingTorchLeft.xml`: priority 10, `Bip01_L_Clavicle` and descendants + `Bip01_Prop2`.
  - **`IsoPlayer.canPerformHandToHandCombat` (~3790) blocks attacks when both hand models have masks.**
- No vanilla clip fires with the left arm.

## Design constraints so far

Added after the melee and firearm inventories:
- **Plain off-hand swing:** an off-hand swing that keeps the hands as they are is possible only in single player:
  `setUseHandWeapon(secondary)` in `OnWeaponSwing`. Several things still come from the primary: animation, swing speed,
  crit / knockdown, knife crits, the weapon-level multiplier, and the condition gate. In MP the hit packets are dropped
  by other clients.
- **An empty primary falls back to a shove:** with the primary empty and a weapon in the off hand,
  `calculateAttackVars` forces shove + bareHands.
- **"Both at once" cannot be two collision checks in one swing.** The second `AttackCollisionCheck` is ignored
  (`ATTACKED`). Either chain two swings (one-two, a hand each) or do the second hit by hand, which has no MP path.
- **The off-hand pistol's flash and tracer only come from the primary.** For two pistols, the only fully vanilla way to
  fire the off-hand gun (flash, tracer, ballistics, ammo, accepted by remote clients) is for it to be the primary for
  that shot.
- **So the candidate core for every feature is "the swinging/firing weapon is the primary for that attack".** It would be
  a fast swap before the attack plus a mirrored clip (hand models drawn so each weapon stays in its own hand). Its costs
  and risks (Equip traffic, `Weapon` / OnEquip churn, model jumps) are listed under EquipPacket above. Prototype it in MP
  before building on it.

- **The off-hand weapon must be the primary while it hits.** A hit only replicates when its weapon is the attacker's
  primary on every machine, so an off-hand swing has to make the swinging weapon the primary for the hit. There are two
  candidate ways:
  - **(a) Swap the hands for the swing** (EquipPacket before the hit, ordered on the same channel, so remote clients
    have the new primary when the hit arrives) and play a **mirrored** clip so the weapon, now on Prop1, still shows in
    the left hand. Every swing then costs a swap and flips the `Weapon` type briefly.
  - **(b) Keep each hand's item and only change `useHandWeapon`.** This is only safe while the primary hand holds that
    same weapon, so it does not help an off-hand weapon. It is useful for the "both" swing's primary half only.
  - Pending: the melee inventory decides whether (a) can be done without the visible jump (hidden right-hand model,
    `hideEquippedHandR`, see ZomboidFixesB42 notes).
- **Extra hits share the per-player anticheat rate budget.** It is 3 hits per 1.2 s per player for a `maxHitCount=1`
  weapon with multi-hit off, and the default action is a kick. A "both" swing that sends two hit packets per swing at a
  fast swing speed can exceed it. Options:
  - pace the double swing (one-two, not simultaneous);
  - merge both weapons' hits into one packet (impossible: one weapon ID per packet);
  - document that servers may need `AntiCheatHit = 3` (Log).
- **Melee condition loss for the off-hand weapon** happens on the server only when the server's primary is a melee
  weapon. With (a) the swap makes it so. Ranged condition loss is client side.
- **Two pistols:**
  - Each shot is a separate hit packet with its own weapon ID, and the server takes ammo per shot in
    `ISReloadWeaponAction.onShoot`.
  - The off-hand gun's shot needs that gun to be the primary on every machine at that moment, the same problem as
    melee. The firearm inventory decides the approach.
- **Remote animation:** custom anim variables (left-hand stance, off-hand swing) need `addVariableToSyncList`, and every
  synced key is re-sent with every player update, so use at most one or two. Otherwise derive the state on each machine
  from things already synced (hand items via EquipPacket, `AttackType`, `CombatSpeed` in the hit packet).

## Open questions (for the user)

- **Primary empty, weapon only in the off hand:** should plain attack swing it automatically (Brutal Handwork did)?
- **Melee primary + handgun secondary:** does modifier + attack fire the off-hand gun alone, or is that "shooting only
  from the off hand", which is not allowed?
- **Off-hand penalties:** accuracy, damage, swing speed and crit for the off hand, and their sandbox options. Should there
  be an "Ambidextrous" trait?
- **XP, endurance and condition** for an off-hand swing and a double swing: each weapon its own skill XP, both lose
  condition, double endurance?
- **Double swing:** simultaneous or a one-two combo? Separate targets per weapon? (This decides the anticheat rate.)
- **Two pistols when one gun is empty or jammed:** does the other still fire? Combined recoil, accuracy penalty and
  noise? Muzzle flash and casings for the off-hand gun? Gunworks / TienMagazineBag compatibility?
- **HUD:** an ammo counter for the off-hand gun.
- **Unarmed fists** (Brutal Handwork had them): in scope?
- **Shove / stomp / knife crits** with two weapons; which hand does a floor attack use?
- **Controller support:** which button is the modifier?
- **Animations:**
  - a left-hand hold pose (Fancy Handwork fixed the holds);
  - mirrored off-hand swings (1handed and knife sets);
  - a double swing;
  - dual-pistol aim and fire.
  These are new clips made offline (the engine cannot mirror).
- **Swap hands:** a timed action with a short duration like vanilla equip, or instant? Usable while aiming?
- **Two-handed weapons, spears, heavy and throwing weapons** are excluded from dual wielding (`WeaponKind`). Confirm.
