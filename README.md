Ratchet & Clank Size Matters Archipelago

This a initial implementation for the PS2 version of the game.

## Current checks include:
- Clank Challanges
- Armour & Titanium Bolt pickups
- Skyboard Challanges
- Weapon Vendors
- Skill Points (untested in full)
- Armour Sets

## Currently Randomized:
- Planets
- Gadgets
- Weapons
- Armour


## Known Bugs and issues
- vendor purchases currently set ratchets active weapon (change to a unlocked weapon)
- vendor purchases sometimes does not display purchasable weapons (for this issue just walk away from the vendor wait a second and open the vendor again)
- Kalidon cutscene forces player to Metalis (after beating the boss load game to get out and not trigger deathlink)
- Challax Cutscene forces player to Dayni Moon (go back into ship to get back into logic, or before starting end Challax cutscene load current save to get back to ship)
- Giant Clank missions are currently not checks except for skill points
- Outpost Omega 1 currently removed from game, until logic for level is completed.
- vendors do not always allow you to buy ammo (spam vendor open menu and you should be able to buy ammo if this happens)


## How to start
To start connect to the client while in the main menu screen for load save, new save and options. Once connected start a new game you should be brought to pokitaru on the ship platform. Both pokitaru and Ryllus are guaranteed starting locations from there on planets are randomized. 

## Massive thanks
The build script and pypine is vendored from [evilwb/pypine](https://github.com/evilwb/pypine). Based on https://projects.govanify.com/govanify/pine. this couldnt have been done without his pcsx2 interface.

Massive inspiration from RAC2 and RAC3 AP's for how to handle Ratchet and Clank games. 
