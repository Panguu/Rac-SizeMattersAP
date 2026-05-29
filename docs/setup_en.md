# Ratchet & Clank: Size Matters Archipelago Setup Guide

## Requirements

- PCSX2 emulator (2.x or later recommended)
- A copy of **Ratchet & Clank: Size Matters** — NTSC-U disc or ISO (`SCUS-97615`)
- The Archipelago client (included with this installation)

---

## Enabling PINE in PCSX2

PINE is the memory interface the client uses to communicate with the emulator.

1. Open PCSX2.
2. Go to **Settings → General Settings** (or **Tools → Settings** depending on your version).
3. Find the **PINE** section and enable it. Leave the slot/port at the default value unless you have a specific reason to change it.
4. Restart PCSX2 if prompted.

---

## Starting a Game

1. Launch the **R&C: Size Matters Client** from the Archipelago launcher.
2. Connect to your Archipelago server with your slot name.
3. In PCSX2, load `SCUS-97615` and start a **New Game**.
4. Play through the opening until you reach **Pokitaru** and have control of Ratchet.
5. The client will automatically connect to PCSX2 once the correct game ID is detected.

> **Important:** Always start from a New Game at the beginning of a seed. Loading a save from a previous run will cause inventory and location state to be out of sync.

---

## Weapons and Gadgets

When the client first connects it will scan PCSX2 memory for the weapon array. This scan can take a moment. You will see a message like:

```
[RAC] Weapon array at 0x20F12345.
```

If weapons or gadgets are not being applied correctly, use the following commands in the client console:

| Command | Description |
|---------|-------------|
| `/scan` | Force a fresh weapon array scan. Use this if weapons are not showing up after connecting or after a game reload. |
| `/reconnect` | Disconnect and reconnect to PCSX2, then re-apply all received items. Use this if the client loses sync with the emulator. |
| `/disconnect_game` | Disconnect from PCSX2 without closing the client. |

---

## Example YAML

```yaml
name: YourName

game: Ratchet & Clank: Size Matters

Ratchet & Clank: Size Matters:

  # Give weapons as individual items (one per weapon).
  # When enabled, weapons are instead granted as Progressive Weapon items
  # in a fixed unlock order, with additional Progressive Weapon items
  # unlocking mod slots for that weapon.
  # 0 = off (individual weapons), 1 = on (progressive)
  progressive_weapons: 0

  # Give armour pieces as individual items (one per piece).
  # When enabled, armour is granted as Progressive Pickup items
  # that unlock pieces in a fixed order per armour set.
  # 0 = off (individual pieces), 1 = on (progressive)
  progressive_armour: 0

  # Treat the 25 skill point challenges as Archipelago location checks.
  # Disabling this removes 25 locations and their corresponding items from the pool.
  # 0 = off, 1 = on (default)
  skill_points_as_checks: 1

  # Number of random weapons you start the game with already in your inventory.
  # Useful if you want to ensure early combat capability.
  # Range: 0–13, default 2
  starting_weapons: 2

  # Number of random gadgets you start the game with.
  # A value of 1 typically grants the Hypershot, which is needed for early progression.
  # Range: 0–8, default 1
  starting_gadgets: 1

  # Amount of bolts added to your inventory each time you receive a Bolts item.
  # Range: 0–100000, default 0
  starting_bolts: 0

  # How many deaths are forgiven before your inventory is wiped on death.
  # 0 = every death wipes inventory (hardest), 5 = very forgiving.
  # Range: 0–5, default 0
  death_amnesty: 0

  # When enabled, dying sends a death signal to all other players in the multiworld
  # who also have Death Link enabled, and receiving one kills you.
  # 0 = off (default), 1 = on
  death_link: 0
```

---

## Troubleshooting

**Client says "Wrong game in PCSX2"**
Make sure you are running `SCUS-97615` (NTSC-U). PAL and other regional versions are not supported.

**Weapons are not appearing after receiving items**
Use `/scan` in the client console. If that does not help, use `/reconnect`.

**Vendor purchases are not registering**
Make sure you are standing at a vendor on a planet that has vendor locations. Purchases are detected when you buy from the vendor menu — the client needs to be connected before you open the menu.
