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
- **2026-10-02 (second session, Windows, game 42.21.0):** research finished and the plan below chosen
  ("The plan: no hand swaps"). Clip mirroring is proven offline (`scripts/anim/mirror.py`, renders in `tmp/anim/`).
  **Nothing has been tried in game yet.** Next step: the in-game prototype listed at the end of the plan.
- **Design:** under discussion with the user (see "Open questions").
- **Decompile:** temporary, in a session scratchpad. Re-create it with the Vineflower recipe in ZomboidFixesB42/CLAUDE.md
  (on Windows: the game's `jre64/bin/java.exe`; extract the jar's `zombie/` with Python `zipfile`, Git Bash `unzip`
  stopped after 135 classes). Line numbers below were taken from 42.20; the ones re-checked in 42.21 (`Weapon.java`,
  `SwipeStatePlayer` 128-134 / 199 / 209, `CombatManager` 518 / 670, `IsoGameCharacter` 16668) have not moved.
- **PZ_Optimization** (installed on this machine) overrides `IsoPlayer`, `IsoGameCharacter`, `AnimationPlayer`,
  `ModelManager` and more from the game folder. Research is done against the vanilla jar, since other players won't
  have it; test in game with it removed too.

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
- **`scripts/anim/`** (python + numpy, Blender 5.2; they import TienInspectWeapon's `scripts/anim` pipeline from the
  sibling repo, so keep both checked out side by side):
  - `xmath.py`: world poses of a clip, the bind pose, L/R bone-name mirroring.
  - `mirror.py <VanillaClip> <out.x> [--prop2 mirror|vanilla]`: writes the left/right mirror of a vanilla Bob clip.
  - `preview2.py` (Blender): renders a clip with a machete on Prop1 (dark) and one on Prop2 (red), views front / q34 /
    top: `"$BL" -b --factory-startup -P scripts/anim/preview2.py -- <clip.x> <abs out dir> every:2`.
- **Not created yet:**
  - `poster.png` / `icon.png` / `preview.png` (mod.info has no poster/icon lines until they exist).
  - `media/AnimSets/player/...` and `media/anims_X/Bob/` (mirrored clips).
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
- *(Superseded by "The plan: no hand swaps" below, kept for the reasoning.)*
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

## Engine findings: sync, masks, input (42.21)

- **Packet order:** VariableSync, Equip, State, AttackCollisionCheck and every PlayerHit* packet are reliability 3
  (RELIABLE_ORDERED) on ordering channel 0 (priority 0 or 1; RakNet assigns the order index at send time). So a synced
  variable set before a swing reaches the server, and is relayed to other clients, before that swing's hit packet.
- **VariableSync** (`VariableSyncPacket`): the server sets the value on **its own copy** of the player (server Lua can
  read it) and relays it at once to every connection `isRelevantTo` the player except the sender. Remote clients set it
  on their copy. No Lua event fires for it anywhere.
- **Cost of a synced key** (`addVariableToSyncList`, a global set shared by all mods): every `setVariable` of it by the
  local player sends a packet, even with an unchanged value, so set it only on change. Every relayed PlayerUpdate is
  followed by one VariableSync per synced key that is non-nil on that player (`PlayerPacket.java:200` →
  `GameServer.setCustomVariables`, sent as a **string**), so use one key with string values. `clearVariable` is not
  synced: write `""` instead.
- **`InventoryItem:setID(id)`** is public, exposed, and only sets the field (no container map to update).
- **Remote hit acceptance** (`fields/hit/Weapon.java`, unchanged in 42.21): bareHands ID first; on a client only
  `getPrimaryHandItem():getID() == id` (an empty primary takes bareHands). A remote client then calls
  `Player.attack()`: `setUseHandWeapon(weapon)`, copies AttackVars and the hit list, `pressedAttack()` (the remote swing
  starts here, when the hit packet arrives), and `startMuzzleFlash` for a ranged weapon.
- **Server side of an off-hand hit** (packet weapon = the secondary, found by ID in the inventory): damage from the
  packet; `OnWeaponHitXp` with the secondary (its skill); `processMaintenanceCheck` passes because the server's
  `useHandWeapon` is the melee primary (`setPrimaryHandItem` sets it; the server never runs the swing) and damages the
  secondary, then `checkSyncItemFields` to the owner; endurance by the secondary. `removeKnife` (jaw stab) removes the
  **primary**, so off-hand swings must never be knife crits. Firearms: `OnWeaponSwingHitPoint` → vanilla
  `ISReloadWeaponAction.onShoot` takes ammo from the packet weapon, so an off-hand shot empties the off-hand gun.
- **Vanilla `attackHook`** checks `canShoot` and plays the shot sound for the primary only; dual pistols need their own
  hook (`Hook.Attack.Remove(ISReloadWeaponAction.attackHook)` + a wrapper).
- **No Lua event for anim events** of the player's states (only timed actions get `animEvent`).
- **Left-hand masks:** `actiongroups/player/<idle|aim|...>/to_maskingleft.xml` enters the `maskingleft` substate while
  `LeftHandMask != ""`; its nodes (priority 10) weight `Bip01_L_Clavicle` + descendants and `Bip01_Prop2`. The swing
  state (`melee`) has no maskingleft child, so masks are off during swings. `LeftHandMask` is set by `ModelManager`
  from the secondary item's script and **cleared only when the hand models are rebuilt**; `IsoPlayer.updateAimingStance`
  sets/clears `RaiseHand` the same way. Lua can set it to its own value (re-set it every tick). It is not synced, so each
  machine sets it for every player from that player's hand items. `canPerformHandToHandCombat` blocks attacks only when
  both hand **models** carry a mask value from their item scripts, which a Lua-set variable does not.
- **Keys** (`shared/keyBinding.lua`): Attack = LMB, Aim = Left Ctrl (alt RMB), Melee (shove) = Space, Rack = X,
  Reload = R, Manual floor attack = Left Alt.

## Animation findings: mirroring (2026-10-02, verified offline)

- **The bind pose is symmetric** across file X within 7 mm. Each Biped left bone's axes are the mirrored right bone's
  turned 180° about Z (`K = (S·B_R·S)^-1·B_L`), the same for centre bones.
- **Mirror formula** (`mirror.py`): `W'_b = S·W_m(b)·S·K_b`, then back to local; props use `K = I` (a weapon model has
  no handedness convention: the long axis (+Y) and the edge (Z) mirror correctly, only the flat side (X) shows its other
  face). Mirroring twice gives the original back within 0.1°. The first try used K = Z180 for the props and pointed
  every blade backwards.
- **Results:** `Bob_Attack1Hand01_Hit`, `Bob_Attack1Hand02_Hit` and `Bob_AttackKnife01_Hit` mirror into clean left-arm
  swings with the blade leading like vanilla's (renders: `tmp/anim/sheet_swings.png`, `tmp/anim/mirror_test.gif`).
- **Grips:** in every vanilla clip Prop2 sits exactly at the idle's left grip (`L_Hand⁻¹·Prop2` constant). Prop1 turns
  in the right hand during swings (13° in 1Hand01, 34° in the knife stab). The mirrored right grip and vanilla's left
  grip agree in position (6 mm) and long axis but differ by a **72° roll about the blade**. Vanilla's left grip is made
  for torches and bags: in vanilla swings an off-hand blade lies across the belly. So:
  - mirrored swings keep the mirrored grip (`--prop2 mirror`); with vanilla's grip the blade trails (`mirV` renders);
  - a dual-wield left hold (a maskingleft node, below) should put Prop2 at the mirrored grip everywhere, so nothing
    rolls when a swing starts;
  - in mirrored swings the **main** weapon (Prop1) inherits the mirrored belly hold; set its track to
    `R_Hand × the idle right grip` (or a guard pose) when building them.
- The file's frame matrices still hold the source clip's first frame (`xanim.py` reports a Prop1 mismatch); the tracks
  override them, as with TienInspectWeapon's clips. Untested in game.
- **Clips to mirror** for melee (from `AnimSets/player/melee/1handed/*.xml`): `Bob_Attack1Hand01_Hit/HitB/HitC`
  (2D blend by AttackVariationX/Y), `_CritHit`, `_Miss`, `Bob_Attack1Hand02_Hit/_CritHit`, `Bob_Attack1Hand03_Hit/_CritHit`,
  `Bob_AttackFloor1Hand`, `Bob_AttackKnife01_Hit`, `Bob_AttackFloorStab`, `Bob_AimToIdle_1Hand` (transition). Knife
  crits are excluded (jaw stab removes the primary). 1HDefault's `AttackCollisionCheck` is at 25% of the clip.

## The plan: no hand swaps (2026-10-02)

The items stay in their hands at all times. Only Lua state changes per attack.

1. **Attacker's client:** the off-hand key (held) sets the one synced variable `TDW_Hand = "L"` (on change only), and
   back to `""` once the swing's hit has been sent (after `AttackCollisionCheck`, e.g. `OnPlayerAttackFinished`). In
   `OnWeaponSwing` (local player, `TDW_Hand == "L"`) call `setUseHandWeapon(secondary)`: damage, range, sounds, hit
   events, packets and condition then follow the off-hand weapon. Override `setCombatSpeed` (it is computed from the
   primary) and clear the crit for knives.
2. **Animation, every machine:** nodes in `melee/1handed` with the vanilla conditions + `TDW_Hand = L` (one more
   condition, so they win) play the mirrored clips. The left weapon is on Prop2 and stays in the left hand, so nothing
   jumps.
3. **Remote clients:** each tick, for every remote player whose `TDW_Hand` is `L`, swap the IDs of the local copies of
   their two hand items (`setID`), and swap back when it returns to `""` (also after an EquipPacket replaces the
   copies). The off-hand hit packet then matches the primary copy: the swing plays, damage lands, the zombie's owner
   keeps the damage. The remote copy used for the hit is the right-hand item, so its hit sound may differ.
   - **Risk:** if `TDW_Hand = L` and the hit packet arrive in the same frame, Lua has not run yet and the hit is dropped
     (vanilla's off-hand behaviour, damage stays on the server). Holding the key gives a lead of reaction time plus the
     25% wind-up, so this should be rare. Measure it in MP.
4. **Server:** nothing to do for melee (see "Server side of an off-hand hit"). Anticheat rate is per player across both
   weapons: pace "both at once" as a one-two.
5. **Idle hold:** each machine sets `LeftHandMask = "TDWDualLeft"` on players holding two 1H weapons; a maskingleft
   node with that condition (bones: L arm + Prop2, priority 10) holds Prop2 at the mirrored grip.
6. **Dual pistols:** a second attack per trigger with `setUseHandWeapon(secondary)`, our own attack hook (ammo/jam check
   and sound of the off-hand gun). Muzzle flash and tracer (see "Off-hand muzzle flash" below): move the primary gun's
   muzzle attachment onto the left gun's muzzle for that shot.
7. **Swap hands key:** one server-run timed action (an EquipPacket chain at the player's pace), no per-attack swaps.

### Gun + melee (42.21)

Routing facts:
- `WeaponType.getWeaponType(chr)` re-sets `rangedWeapon` from the **primary** on every call (swing speed, weapon level,
  timed actions, thermoregulator...), so Lua cannot override it: a handgun primary sends every attack through the
  `ranged` action group (`idle|aim/to_ranged.xml`: initiateAttack + rangedWeapon + not bDoShove), a melee primary
  through `melee`. Both run `SwipeStatePlayer`; our nodes go in whichever group the primary picks.
- Gun or melee is decided **per attacking weapon** (`weapon.isAimedFirearm()` on `useHandWeapon`) in
  `attackCollisionCheck` (~686: flash, ballistics, `fireWeapon`) and `calculateHitListWeapon` (range =
  `weapon:getMaxRange(owner)`, re-run at the collision event). `AttackVars` holds no weapon: `getWeapon` returns
  `useHandWeapon` unless the bare-hands flag is set.
- `pressedAttack` (CombatManager 3140): starts only if `isDoShove() or isWeaponReady()`; `isRangedWeaponReady` fails
  when `useHandWeapon` is an aimed firearm and the **primary's model script** has no `muzzle` attachment. With a ranged
  primary (`WeaponType` HANDGUN) it sets the recoil delay from `useHandWeapon` and sends `PlayerEmptyShot` when
  `useHandWeapon:getCurrentAmmoCount() == 0` (a melee weapon always is). Other clients answer `PlayerEmptyShot` by
  starting an attack if their copy's weapon is an aimed firearm.
- Ballistics run per frame only while `useHandWeapon` is an aimed firearm and the player aims
  (`IsoGameCharacter` ~9160, also turns the player to the reticle); `CanAttack` resets `useHandWeapon` to the primary
  every input frame. Remote clients start the flash from any hit packet that carries tracers (`PlayerHit.processTracers`)
  and draw the tracers from the shooter's recorded start points. Zombie hit reactions travel in the packet.

**Handgun primary + melee off-hand (off-hand melee swing): workable.**
- Our `Hook.Attack` replaces vanilla's `attackHook` for this case (no gunshot sound, noise or `canShoot`); raise the
  melee item's ammo count to 1 around `DoAttack` so `pressedAttack` sends no `PlayerEmptyShot`, then put it back.
- `OnWeaponSwing` → `setUseHandWeapon(secondary)`: melee hit list with the knife's own range, melee packets, no flash.
- Nodes in `AnimSets/player/ranged/handgun/` with `TDW_Hand = L` play the mirrored melee clips.
- Server: condition loss needs `isActuallyAttackingWithMeleeWeapon`, which fails (the server's `useHandWeapon` is the
  gun). `WeaponHit.process` fires `OnWeaponHitXp` right before `processMaintenanceCheck`, so a server handler sets
  `player:setUseHandWeapon(weapon)` there when `weapon` is the secondary (put it back next tick). Object hits (doors,
  windows) have no event first: no condition loss there.
- Remote clients (ID swap): their weapon is the pistol copy, so `Player.attack` starts a muzzle flash (light + flash
  model). Set the copy's `setMuzzleFlashModelKey(nil)` while `TDW_Hand = L`; the 6-tick light on the tile remains.
- Hold pose: the vanilla handgun aim supports the gun with the left hand. A maskingleft node (L arm + Prop2) keeps the
  melee weapon in a low guard while aiming; vanilla's `aimhandguntorchleft*.xml` is the model (torch in the left hand,
  one-handed pistol aim).

**Melee primary + handgun off-hand (off-hand shot): fights the engine.** The gun shot needs a `muzzle` attachment on the
melee primary's model script (`ModelScript:addAttachment(ModelAttachment.new("muzzle"))`, placed at the left gun's
muzzle in Prop1 space) or `pressedAttack` refuses and ballistics find no targets, and the melee item's
`setMuzzleFlashModelKey` for a flash. The reticle, auto-facing, aim delay and accuracy all follow `useHandWeapon`, which
`CanAttack` resets to the melee primary every frame, so the player would aim with melee rules. Better: the off-hand key
**swaps hands** for this pair (one Equip each way at the player's pace, not per shot), so the gun is the primary while
aiming and everything is vanilla. Keep the gun drawn in the left hand with crossed-prop aim clips (Prop1 at the left
hand, valid while the clip dominates) or accept the visible switch. Needs the user's call (open questions).

### Dual pistols: two bullets per trigger pull (42.21, the user's choice 2026-10-02)

- **Chosen:** each pull fires the main gun normally, then the off-hand gun as a second attack. Each bullet leaves its own
  muzzle (off-hand: muzzle redirect, see below) along its own barrel. Parallel barrels are fine (bullets pass about
  20 cm either side of the aim point), so the converging-aim work below is optional polish.
- **Why not one attack:** one attack has one bullet origin. Multi-projectile shots (`ProjectileCount`, used only on
  the `isRangeFalloff` path in `fireWeapon`) spread every pellet from the one muzzle. A second `AttackCollisionCheck`
  in the same swing is ignored (`ATTACKED`, reset only in `SwipeStatePlayer.enter`). Possible but worse fallback: the
  primary with `setProjectileCount(2)` + range falloff for one pull, both lines from the right gun, the left gun's ammo
  handled by our code (`HandWeapon:setProjectileCount` is public; the anticheat then allows `2 × MaxHitCount`).
  The user is trying this one (2026-10-02). What the code does with it:
  - `ProjectileCount` is read **only when `isRangeFalloff()`** (CombatManager 2161, 3568, `fireWeapon`); a pistol's
    script has RangeFalloff off, so also call `setRangeFalloff(true)` (public).
  - Pellets come from native `getSpreadData(range, ProjectileSpread × scale, ProjectileWeightCenter, count)`. A pistol's
    `ProjectileSpread` is 0 (not in its script), so both pellets follow one line; the target then gets one HitInfo per
    pellet that hit it (`spreadCount`, ~2220), i.e. two hits on the same zombie. For a chance of two different targets
    set a small `setProjectileSpread` and `setMaxHitCount(2)` (`Base.Pistol` MaxHitCount = 1 caps the ranged hit list).
  - Other falloff-path effects: hit force `rangeDel` 2.0 instead of 1.0 (~1011), no piercing damage reduction (~786), one
    tracer per pellet from the right muzzle, in SP only the first hit of the shot gives XP (~1162).
  - None of `projectileCount`, `projectileSpread`, `rangeFalloff`, `maxHitCount` is saved or sent: `Item.InstanceItem`
    copies them from the script (1664, 1719), so every network copy and every reload is back to the script values.
    **Set them on the server's copy too**: the anticheat reads the server copy's `ProjectileCount × MaxHitCount`; with 1,
    a 2-pellet packet adds two entries and two pulls inside 450 ms make 4 > 3 (two violations kick).
  - Ammo: vanilla `onShoot` takes one round from the primary only; the left gun's round, chamber and jam are ours
    (server side + `syncHandWeaponFields`); drop back to 1 projectile when the left gun is empty or jammed.
  - `-debug` has a Firearm debug window with a "Projectile Count" slider (`debug/debugWindows/FirearmPanel.java`).
- **When the second attack can start:** `attackStarted` is cleared in `SwipeStatePlayer.exit` (446), and `CanAttack`
  waits for the `AttackAnim` FALSE event. Vanilla's `Bob_AttackHandgun` is 0.67 s (shot at 0.1% of it, `ShotDone` at
  90%), so use our own short dual fire clip with an early `AttackAnim` FALSE and `m_EarlyTransitionOut`. Trigger the
  second attack from Lua on the next tick after `OnPlayerAttackFinished` (fires in `exit`, 468), not inside it.
- **Anticheat sets the minimum gap.** `AntiCheatHitWeapon.isRateExceeded` → `AttackRateChecker.check`: an aimed
  single-fire gun gets a 450 ms window (3 × 150 ms), and the check fails once it holds more than `3 × maxHits` hit
  entries. `maxHits = ProjectileCount × MaxHitCount` (vanilla `Base.Pistol`: 1 × 1), or at least 3 with sandbox
  MultiHitZombies. So with multi-hit off, **more than 3 hits in 450 ms per player** is a violation; two violations kick
  by default. Only real hits count (PlayerHitSquare, i.e. misses, has no HitWeapon check). Keep every bullet
  **more than 150 ms** after the previous one (e.g. 160 ms, entries exactly 150 ms apart still make 4 in the window):
  the pair sounds like a quick "ba-bang", and the cap is about 6 bullets a second.

### Dual-pistol aim that lines up with both guns (42.21)

- **How vanilla aims:** `IsoPlayer.setAngleFromAim` (every frame while aiming a firearm) faces the character from its
  centre (`getAimOriginPosX/Y` = position) towards the reticle point (`calculateAimVector`), and
  `BallisticsController.updateAimingVector` sets `verticalAimAngle` from chest height (`getZ() + 0.495`) to the target.
- **What the bullet system gets** (`BallisticsController.update`): the muzzle position (the primary model's `muzzle`
  attachment, moved back along the barrel onto the plane through the character's centre), the muzzle direction and the
  reticle position, all sent to native `Bullet` (PZBullet64.dll, closed). The target is the native hit if there is one,
  else muzzle + direction × range. Tracers run from the muzzle position. Vanilla's one-gun aim pose keeps the gun near
  the centre line, so barrel and aim line agree.
- **Dual aim pose:** author both barrels **toed in** so they cross the centre line at the aim point. Each shot then
  leaves its own muzzle and meets the reticle, and the tracers converge there.
  - The handgun aim node (`aim/aim_handgun.xml`) is a 2D blend with X = `verticalAimAngle` (5 clips: Down75, Down, mid,
    Up45, Up75). Our dual node can use X = `verticalAimAngle`, Y = a Lua-set float for the aim distance (near/far toe-in),
    so 10 clips.
  - Build them with TienInspectWeapon's `rig.py` (weapon-first keys + two-bone IK): place each gun so its barrel points
    at the convergence point, then IK the arms. Square stance, not vanilla's 31° bladed pelvis.
  - Aim distance on the attacker's client: `AimingReticle` is not exposed, but `getMouseX/Y` and `IsoUtils.XToIso/YToIso`
    are. A gamepad's reticle is private, so use a fixed distance there. Other players' screens use a fixed distance (or
    2-3 steps synced only on change), since tracers arrive with their start points anyway.
- **Muzzle redirect per shot:** the offset and rotation written into the primary's `muzzle` attachment (Prop1 space) for
  an off-hand shot = `Prop1⁻¹ · Prop2 · left muzzle`. This depends on the blend, so bake it per clip at build time and
  interpolate in Lua from `verticalAimAngle` and the distance value.
- **Untested:** whether native `Bullet` picks targets along the muzzle direction or near the reticle. With converging
  barrels both agree. Check with `-debug` and DebugOptions `physicsRenderBallisticsControllers`.

### Off-hand muzzle flash and tracer (42.21)

- The engine flash is drawn only on `primaryHandModel` (`ModelSlotRenderData.initModelInst` ~215 →
  `EffectsManager.initMuzzleFlashModel`), as the primary item's `getMuzzleFlashModelKey()` model on its `muzzle`
  attachment, for 0.04 s, one effect per character. Its light is a plain `IsoLightSource(x, y, z, r, g, b, 18, life 6)`
  on the character's tile added to `getCell():getLamppostPositions()` (`IsoLightSource` is exposed).
- The `muzzle` attachment is read **live** from the model script every time (`ModelInstance.getAttachmentById` →
  `modelScript.getAttachmentById`), and `BallisticsController` (~86, ~194) reads the same one for the bullet origin, the
  aim ray and the tracer. `ModelScript` and `ModelAttachment` are exposed and `getOffset()` / `getRotate()` return mutable
  `Vector3f`s (degrees for rotate). So Lua can set, for one shot,
  `getScriptManager():getModelScript(<primary gun model>):getAttachmentById("muzzle"):getOffset():set(...)` to the left
  gun's muzzle expressed in Prop1 space (`Prop1⁻¹ · Prop2 · left gun muzzle`, taken from our own dual-pistol fire clip at
  the shot frame), and restore it afterwards. The engine then draws its real 3D flash, the tracer and the bullet ray from
  the left gun. `HandWeapon:setMuzzleFlashModelKey(nil)` (public) switches the flash model off instead, if wanted.
- Caveats: the model script is shared by every gun of that model on that client, so another player firing the same gun
  model right-handed inside the window gets the displaced point; restore the offset every tick as a safety net. Remote
  clients start the flash from the hit packet (`Player.attack`), so they apply the same offset while that player's
  `TDW_Hand` is `L`. The relative pose of the two guns must be the same in every aim clip we author (vertical aim blends
  included). Untested in game.
- Fallback with no engine help: a sprite (`media/textures/weapons/firearm/fx/muzzle_flash_0N.png`) drawn in
  `OnPreUIDraw` at `isoToScreenX/Y` of the muzzle position computed from the player's position, facing and our clip
  (Lua cannot read bone positions: `AnimationPlayer` is not exposed). It draws over walls and characters.

**In-game prototype, in order:** (a) one mirrored clip + node keyed on `TDW_Hand`, set by a debug key, in SP: does the
node win and the weapon stay in the left hand; (b) `setUseHandWeapon(secondary)` in SP: damage, condition, XP from the
off-hand weapon; (c) MP with two clients (`TienGiveItemMP` mptest on the Mac, or two Steam/non-Steam clients here):
remote swing visible, zombie health stays, ID swap timing.

## Open questions (for the user)

- **Primary empty, weapon only in the off hand:** should plain attack swing it automatically (Brutal Handwork did)?
- **Melee primary + handgun secondary:** does modifier + attack fire the off-hand gun alone, or is that "shooting only
  from the off hand", which is not allowed? If allowed: swap hands while the off-hand key is held (recommended, see
  "Gun + melee"), or fire from the off hand with melee aiming rules?
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
