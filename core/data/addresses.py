from dataclasses import dataclass

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
CHALLENGE_MODE_ADDRESS = 0x21F4C778 # 1 - 255 when challange mode is active, 0 otherwise
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

DAYNI_MOON_CLANK_CHALLENGES_COMPLETED_ADDR: dict[str, int] = {
    "Two's A Crowd": 0x1F4B400,
    "Reverse Into Victory": 0x1F4B401,
    "Emergency Bridge": 0x1F4B402,
    "Leap Of Faith": 0x1F4B403,
    "Infinite Improbability": 0x1F4B404,
    "Welcome to Dayni": 0x1F4B3F6,
    "Round Up!": 0x1F4B3F7,
    "Variety Is Shocking": 0x1F4B3F8,
    "Tom Sawyer": 0x1F4B3F9,
    "Smasherbot Returns!": 0x1F4B3FA,
    "Tri-bomb Tournament": 0x1F4B3FC,
    "A-rooouund the Bend": 0x1F4B3FD,
    "The Thin Bouncy Line": 0x1F4B3FE,
    "The Ultimate Showdown": 0x1F4B3FF,
}
# each address is 4 bytes
QUICK_SELECT_ADDRESSES: dict[str, int] = {
    "right": 0x21F4B364,
    "top-right": 0x21F4B368,
    "top-middle": 0x21F4B36C,
    "top-left": 0x21F4B370,
    "left": 0x21F4B374,
    "bottom-left": 0x21F4B378,
    "bottom-middle": 0x21F4B37C,
    "bottom-right": 0x21F4B380,
}

CURRENT_WEAPON_IN_VENDOR = 0x21F4AB8C
# This address designates what appears in vendor, i.e how many options there are in the menu.
WEAPON_VENDOR_SLOTS = 0x21F4ABE4
# each item is 4 bytes: 02 00 00 00 is lacerator
WEAPON_VENDOR_ITEMS = 0x21F4AB80
# Metalis challenge unlock addresses — layout per byte is undocumented.
# 0x1F4B3DB = unknown challenge type 1 unlock
# 0x1F4B3DC = unknown challenge type 2 unlock
# 0x1F4B3DD = unknown challenge type 3 unlock
# All three are written as a single 3-byte value (0x0FFFFF).
METALIS_CLANK_CHALLENGES_UNLOCK_ADDR: int = 0x1F4B3DB

# Dayni Moon challenge unlock addresses — each byte unlocks a specific challenge type.
DAYNI_MOON_DERBY_CHALLENGES_UNLOCK_ADDR:     int = 0x1F4B3F3  # Derby challenges
DAYNI_MOON_DERBY_B_CHALLENGES_UNLOCK_ADDR:   int = 0x1F4B3F4  # Derby challenges (second type)
DAYNI_MOON_GADGETBOT_CHALLENGES_UNLOCK_ADDR: int = 0x1F4B3F5  # Gadgetbot challenges
DAYNI_MOON_CLANK_CHALLENGES_UNLOCK_ADDR:     int = DAYNI_MOON_DERBY_CHALLENGES_UNLOCK_ADDR

METALIS_CLANK_CHALLENGES_COMPLETED_ADDR: dict[str, int] = {
    "Buzzsaw Blitz": 0x1F4B3DE,
    "Take Two For The Team": 0x1F4B3E8,
    "CHARGE!": 0x1F4B3DF,
    "Bridge The Gap": 0x1F4B3E9,
    "Electric Boogaloo": 0x1F4B3E0,
    "Of Trapeze and Teleporters": 0x1F4B3EA,
    "Showdown": 0x1F4B3E1,
    "Brain Trip": 0x1F4B3EB,
    "Smasherbot's Revenge": 0x1F4B3E2,
    "Nigh Impossible": 0x1F4B3EC,
    "Little League": 0x1F4B3E3,
    "Varsity Bracket": 0x1F4B3E4,
    "Collegiate Division": 0x1F4B3E5,
    "Professional Level": 0x1F4B3E6,
    "The Uber Finals": 0x1F4B3E7,
}

# Single address per planet, cumulative bitmask per race.
# Cumulative values: race 1=0x01, race 2=0x05, race 3=0x15, race 4=0x55.
# Each entry is (address, detection_mask) — the NEW bit set when that race completes.
KAILDON_SKYBOARD_CHALLENGES_COMPLETED_ADDR: dict[str, tuple[int, int, int]] = {
    "Learner's Permit":   (0x1F4B407, 0x1F4B408, 0x01),
    "Speeding Ticket":    (0x1F4B407, 0x1F4B408, 0x04),
    "Tricky Air":         (0x1F4B407, 0x1F4B408, 0x10),
    "Master's Challenge": (0x1F4B407, 0x1F4B408, 0x40),
}


OUTPOST_OMEGA_SKYBOARD_CHALLENGES_COMPLETED_ADDR: dict[str, tuple[int, int, int]] = {
    "Interior Decorating": (0x1F4B409, 0x1F4B40A, 0x01),  # address unknown
    "Danger, High Voltage": (0x1F4B409, 0x1F4B40A, 0x04),  # address unknown
    "The Vortex":           (0x1F4B409, 0x1F4B40A, 0x10),  # address unknown
    "Vertigo":              (0x1F4B409, 0x1F4B40A, 0x40),  # address unknown
}
