ARMOUR_BASE                = 0x21F4B354
ARMOUR_SET_COLLECTED_ADDR  = 0x21F4B442  # byte 0: pure sets (bit N = ArmourSets(N+1) complete)
                                           # byte 1 (0x21F4B443): hybrid sets equipped —
                                           #   0x01=Shock Crystal  0x02=Wildburst  0x04=Triple Wave
                                           #   0x08=Ice II         0x10=Stalker
TITANIUM_BOLT_BASE     = 0x21F4B444
SKILL_POINTS           = 0x21F4B437
CHEATS                 = 0x21F4C440
CURRENT_PLANET_ADDRESS = 0x21F4C76C
PLAYER_BOLT_COUNT      = 0x21F4C768
BOLT_PICKUP_MASK       = 0x000000FFFFFFFFFF
PLANET_LOAD_ADDRESS    = 0x21F4C770
CONTROLLER_PAUSE_SELECT_ADDRESS = 0x20F7F414
CONTROLLER_BUTTONS_ADDRESS = 0x20F7F415
PLANET_UNLOCK_ADDRESSES: dict[str, int] = { # each value must be 3 in order to unlock next planet
    "POKITARU":     0x21F4C661,
    "RYLLUS":       0x21F4C662,
    "KALIDON":      0x21F4C663,
    "METALIS":      0x21F4C664,
    "DREAMTIME":    0x21F4C665,
    "OUTPOST_OMEGA":0x21F4C666,
    "CHALLAX":      0x21F4C667,
    "DAYNI_MOON":   0x21F4C668,
    "INSIDE_CLANK": 0x21F4C669,
    "QUODRONA":     0x21F4C66A,
}
# Each planet has a parallel "state" byte at unlock_address + PLANET_STATE_OFFSET.
# e.g. OUTPOST_OMEGA state = 0x21F4C677; gates Outpost Omega 2 (0x17) access.
PLANET_STATE_OFFSET: int = 0x11
# Per-planet player state/health addresses
PLAYER_ADDRS: dict[int, tuple[int, int]] = {
    0x01: (0x20F805C0, 0x20F80E2C),  # pokitaru
    0x02: (0x20F7F2D0, 0x20F7FB3C),  # ryllus
    0x03: (0x20F7F440, 0x20F7FCAC),  # kalidon
    0x04: (0x20F7EDD0, 0x20F7F63C),  # metalis
    0x05: (0x20F762C0, 0x20F76B2C),  # dreamtime
    0x06: (0x20F81B40, 0x20F823AC),  # outpost omega
    0x17: (0x20F82A40, 0x20F823AC),  # outpost omega 2
    0x07: (0x20F806C0, 0x20F80F2C),  # challax
    0x08: (0x20F79850, 0x20F7A0BC),  # dayni moon
    0x09: (0x20F82540, 0x20F82DAC),  # inside clank
    0x0A: (0x20F809C0, 0x20F8122C),  # quodrona
}
PLAYER_STATE  = 0x20F805C0  # fallback when planet not in PLAYER_ADDRS
PLAYER_HEALTH = 0x20F80E2C

# Vendor menu state address per planet (0x09=GadgetTron, 0x0E=Mod Vendor)
MENU_ADDR_BY_PLANET_ID: dict[int, int] = {
    0x01: 0x1073DC0,   # pokitaru
    0x02: 0x1072AC0,   # ryllus
    0x03: 0x1072C40,   # kalidon
    0x04: 0x10725C0,   # metalis
    0x05: 0x1069C80,   # dreamtime
    0x07: 0x1073EC0,   # challax
    0x08: 0x106D040,   # dayni moon
    0x0A: 0x10741C0,   # quodrona
    0x17: 0x107A200,   # outpost omega 2
}

# Goes to 0x13 when the player can interact with the vendor
PRELOAD_MENU_ADDR_BY_PLANET_ID: dict[int, int] = {
    0x01: 0xF4C8C0,    # pokitaru
    0x02: 0xF49080,    # ryllus
    0x03: 0xF48F40,    # kalidon
    0x04: 0xF49D80,    # metalis
    0x05: 0xF45C40,    # dreamtime
    0x07: 0xF4B3C0,    # challax
    0x08: 0xF3F780,    # dayni moon
    0x0A: 0xF4C8C0,    # quodrona
    0x17: 0xF54CC0,    # outpost omega 2
}

# Lacerator unlock address per planet (slot 0, offset 0x45 within struct).
# All other weapon/gadget addresses are derived from these via build_weapons().
_LACERATOR_UNLOCK: dict[int, int] = {
    0x01: 0x20F3EA5C,  # Pokitaru
    0x02: 0x20F3AEDC,  # Ryllus
    0x03: 0x20F3B0DC,  # Kalidon
    0x04: 0x20F3BBDC,  # Metalis
    0x05: 0x20F37DDC,  # Dreamtime
    0x06: 0x20F4215C,  # Outpost Omega
    0x07: 0x20F3D55C,  # Challax
    0x08: 0x20F315DC,  # Dayni Moon
    0x09: 0x20F4305C,  # Inside Clank
    0x0A: 0x20F3EA5C,  # Quodrona (shares layout with Pokitaru)
    0x17: 0x20F46E5C,  # Outpost Omega 2
}
_UNLOCKED_OFFSET = 0x45
WEAPON_ARRAY_BASE_BY_PLANET: dict[int, int] = {
    planet: addr - _UNLOCKED_OFFSET
    for planet, addr in _LACERATOR_UNLOCK.items()
}

CURRENT_WEAPON_IN_VENDOR = 0x21F4AB8C
WEAPON_VENDOR_SLOTS      = 0x21F4ABE4
WEAPON_VENDOR_ITEMS      = 0x21F4AB80


# 2-byte mission progress value per planet, ordered by game progression.
# Addresses confirmed for first three planets; remainder follow the +0x02 pattern.
PLANET_MISSION_ADDRESSES: dict[str, int] = {
    "Pokitaru":        0x21F4B3C4,
    "Ryllus":          0x21F4B3C6,
    "Kalidon":         0x21F4B3C8,
    "Metalis":         0x21F4B3CA,
    "Dreamtime":       0x21F4B3CC,
    "Outpost Omega":   0x21F4B3CE,
    "Challax":         0x21F4B3D0,
    "Dayni Moon":      0x21F4B3D2,
    "Inside Clank":    0x21F4B3D4,
    "Quodrona":        0x21F4B3D6,
}
