# Ratchet & Clank Size Matters Archipelago

This is an initial implementation for the PS2 version of the game. You can find the setup guide [here](docs/setup_en.md).

## Known Bugs and issues
- vendor purchases currently set ratchets active weapon (change to a unlocked weapon)
- vendor purchases sometimes does not display purchasable weapons (for this issue just walk away from the vendor wait a second and open the vendor again)
- Kalidon cutscene forces player to Metalis (after beating the boss load game to get out and not trigger deathlink)
- Challax Cutscene forces player to Dayni Moon (go back into ship to get back into logic, or before starting end Challax cutscene load current save to get back to ship)
- Giant Clank missions are currently not checks except for skill points
- Outpost Omega 1 currently removed from game, until logic for level is completed.
- Vendors do not always allow you to buy ammo (spam vendor open menu and you should be able to buy ammo if this happens)

## Massive thanks
The build script and pypine is vendored from [evilwb/pypine](https://github.com/evilwb/pypine). Based on https://projects.govanify.com/govanify/pine. this couldnt have been done without his pcsx2 interface.

Massive inspiration from RAC2 and RAC3 AP's for how to handle Ratchet and Clank games.