from __future__ import annotations

from ..addresses import PLANET_MISSION_ADDRESSES as _ADDRS

# Maps (address, xor_mask) -> mission_name.
# Detection: (current_value & xor_mask) != 0
# xor_mask is the exact bit(s) that flip when this mission completes.
# xor_mask of 0x0000 means the value is not yet validated — these missions
# will be skipped by MissionsState until filled in.
#
# Two mission types per planet:
#   Story      — main narrative objectives, progress gate the next planet.
#   Additional — optional side objectives that run alongside the story.

# Bits that must be force-written on initial load (not location checks).
PRESET_MISSION_BITS: list[tuple[int, int]] = [
    (_ADDRS["Pokitaru"], 0x0004),   # Rescue the girl
    (_ADDRS["Kalidon"],  0x0004),   # Search the factory
    (_ADDRS["Challax"],  0x0004),   # Explore the miniature city
]

MISSION_COMPLETE_MAP: dict[tuple[int, int], str] = {
    # ── Pokitaru ──────────────────────────────────────────────────────────────
    # story
    (_ADDRS["Pokitaru"], 0x0002): "Fight some robots",
    # "Rescue the girl" (0x0004) is preset on initial load — not a location check
    # additional — pending validation

    # ── Ryllus ────────────────────────────────────────────────────────────────
    # additional
    (_ADDRS["Ryllus"],   0x0002): "Buzzing Cameras",
    # story
    (_ADDRS["Ryllus"],   0x0008): "Investigate the artifact",
    (_ADDRS["Ryllus"],   0x0010): "Unlock the temple",

    # ── Kalidon ───────────────────────────────────────────────────────────────
    # additional — pending validation
    # story
    (_ADDRS["Kalidon"],  0x0008): "Explore the planet",
    (_ADDRS["Kalidon"],  0x0010): "Win the skyboard race",
    # "Search the factory" (0x0004) is preset on initial load — not a location check

    # ── Metalis ───────────────────────────────────────────────────────────────
    # additional — pending validation
    # story — pending validation
    (_ADDRS["Metalis"],       0x0002): "Survive Robot War III",
    (_ADDRS["Metalis"],       0x0004): "Escape the planet",

    # ── Dreamtime ─────────────────────────────────────────────────────────────
    # additional — pending validation
    # story — pending validation
    # story
    (_ADDRS["Dreamtime"],     0x0004): "??????????",

    # ── Outpost Omega ─────────────────────────────────────────────────────────
    # additional
    (_ADDRS["Outpost Omega"], 0x0002): "Escape from facility pt 1",
    # story — pending validation
    (_ADDRS["Outpost Omega"], 0x0080): "Escape the medical facility",
    (_ADDRS["Outpost Omega"], 0x0010): "Rematch - Skyboard racers",

    # ── Challax ───────────────────────────────────────────────────────────────
    # additional
    (_ADDRS["Challax"],       0x0010): "Start giant clank",
    # story
    (_ADDRS["Challax"],       0x0020): "Destroy the space fortress",
    # "Explore the miniature city" (0x0004) is preset on initial load — not a location check

    # ── Dayni Moon ────────────────────────────────────────────────────────────
    # story
    (_ADDRS["Dayni Moon"],    0x0008): "Catch Luna",
    # additional
    (_ADDRS["Dayni Moon"],    0x0010): "Luna fight pt 1",
    (_ADDRS["Dayni Moon"],    0x0002): "Luna fight pt 2",
    # story
    (_ADDRS["Dayni Moon"],    0x0004): "'Disable' Luna",
    (_ADDRS["Dayni Moon"],    0x0020): "Escape from clank",

    # ── Inside Clank ──────────────────────────────────────────────────────────
    # additional — pending validation
    # story
    (_ADDRS["Inside Clank"],  0x0002): "Defeat all technomites",

    # ── Quodrona ──────────────────────────────────────────────────────────────
    # additional
    (_ADDRS["Quodrona"],      0x0008): "Clone Wars",
    (_ADDRS["Quodrona"],      0x0010): "Runnnn from Otto",
    (_ADDRS["Quodrona"],      0x0020): "Defeat mecha Otto",
    # story — pending validation
    (_ADDRS["Quodrona"],      0x0004): "Find Otto Destruct",
    (_ADDRS["Quodrona"],      0x0140): "Defeat Otto Destruct",
}

# Only missions with a known (non-zero) xor_mask.
VALIDATED_MISSION_MAP: dict[tuple[int, int], str] = {
    k: v for k, v in MISSION_COMPLETE_MAP.items() if k[1] != 0x0000
}
