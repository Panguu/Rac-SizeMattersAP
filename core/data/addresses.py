from dataclasses import dataclass

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

# value 3f37 when vendor text is loaded; value 01 when text is on screen
@dataclass(frozen=True)
class DisplayedTextBox:
    planet_id: int
    message_str_pointer: int
    is_visible: int
    vendor_value: int
    countdown_timer: int
TextBoxDisplayAddrs: list[DisplayedTextBox] = [
    DisplayedTextBox(planet_id=0x01, message_str_pointer=0xF47A10, is_visible=0xF47A08, vendor_value=0xBF48, countdown_timer=0xF479E8), # pokitaru  # noqa: E501
    DisplayedTextBox(planet_id=0x02, message_str_pointer=0xF441D0, is_visible=0xF441C8, vendor_value=0xBF35, countdown_timer=0xF441A8), # ryllus  # noqa: E501
    DisplayedTextBox(planet_id=0x03, message_str_pointer=0xF44090, is_visible=0xF44088, vendor_value=0x3F37, countdown_timer=0xF44068), # kalidon  # noqa: E501
    DisplayedTextBox(planet_id=0x04, message_str_pointer=0xF44ED0, is_visible=0xF44EC8, vendor_value=0x3F30, countdown_timer=0xF44EA8), # metalis  # noqa: E501
    DisplayedTextBox(planet_id=0x05, message_str_pointer=0xF40D90, is_visible=0xF40D88, vendor_value=0x7FA7, countdown_timer=0xF40D68), # dreamtime  # noqa: E501
    DisplayedTextBox(planet_id=0x07, message_str_pointer=0xF46510, is_visible=0xF46508, vendor_value=0xBF49, countdown_timer=0xF464E8), # challax  # noqa: E501
    DisplayedTextBox(planet_id=0x08, message_str_pointer=0xF3A8D0, is_visible=0xF3A8C8, vendor_value=0x3FDB, countdown_timer=0xF3A8A8), # dayni moon  # noqa: E501
    DisplayedTextBox(planet_id=0x09, message_str_pointer=0xF4C010, is_visible=0xF4C008, vendor_value=0x3F68, countdown_timer=0xF4BFE8), # inside clank  # noqa: E501
    DisplayedTextBox(planet_id=0x0A, message_str_pointer=0xF47A10, is_visible=0xF47A08, vendor_value=0xBF4C, countdown_timer=0xF479E8), # quodrona  # noqa: E501
    DisplayedTextBox(planet_id=0x17, message_str_pointer=0xF4FE10, is_visible=0xF4FE08, vendor_value=0x3f37, countdown_timer=0xF4FDE8), # outpost omega 2 unknown vendor  # noqa: E501
]


