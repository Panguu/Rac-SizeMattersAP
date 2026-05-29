ARMOUR_BASE            = 0x21F4B354
TITANIUM_BOLT_BASE     = 0x21F4B444
SKILL_POINTS           = 0x21F4B437
CHEATS                 = 0x21F4C440
CURRENT_PLANET_ADDRESS = 0x21F4C76C
PLAYER_BOLT_COUNT      = 0x21F4C768
PLANET_LOAD_ADDRESS    = 0x21F4C770

# Per-planet player state/health addresses
PLAYER_ADDRS: dict[int, tuple[int, int]] = {
    0x01: (0x20F805C0, 0x20F80E2C),  # pokitaru
    0x02: (0x20F7F2D0, 0x20F7FB3C),  # ryllus
    0x03: (0x20F7F440, 0x20F7FCAC),  # kalidon
    0x04: (0x20F7EDD0, 0x20F7F63C),  # metalis
    0x05: (0x20F762C0, 0x20F76B2C),  # dreamtime
    0x06: (0x20F81B40, 0x20F823AC),  # outpost omega
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
# Pokitaru 4 Vendor Items
# Ryllus 1 Vendor Item
# Kalidon 1 Vendor Item

