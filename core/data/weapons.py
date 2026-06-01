import struct as _struct

WEAPON_STRUCT_SIZE = 0x58
WEAPON_MIN_CONSECUTIVE = 4

WEAPON_MOD_COUNTS: dict[str, int] = {
    "lacerator":       2,
    "concussion_gun":  3,
    "acid_bomb_glove": 2,
    "agents_of_doom":  2,
    "bee_mine_glove":  2,
    "static_barrier":  2,
    "shock_rocket":    3,
    "sniper_mine":     2,
    "scorcher":        2,
    "laser_tracer":    2,
    "suck_cannon":     0,
    "mootator":        0,
    "ryno":            0,
}


def is_weapon_candidate(data: bytes, i: int) -> bool:
    if i + 0x46 > len(data):
        return False
    if data[i + 0x3D] > 1 or data[i + 0x3E] > 1 or data[i + 0x3F] > 1:
        return False
    if data[i + 0x45] > 1:
        return False
    level, = _struct.unpack_from("<I", data, i + 0x2D)
    if level > 7:
        return False
    ammo, = _struct.unpack_from("<I", data, i + 0x31)
    if ammo > 9999:
        return False
    icon, = _struct.unpack_from("<I", data, i + 0x1D)
    if icon == 0:
        return False
    return True


def is_ps2_weapon_candidate(data: bytes, i: int) -> bool:
    if i + 0x46 > len(data):
        return False
    if data[i + 0x3D] > 1 or data[i + 0x3E] > 1 or data[i + 0x3F] > 1:
        return False
    if data[i + 0x45] > 1:
        return False
    level, = _struct.unpack_from("<I", data, i + 0x2D)
    if level > 7:
        return False
    ammo, = _struct.unpack_from("<I", data, i + 0x31)
    if ammo > 9999:
        return False
    icon, = _struct.unpack_from("<I", data, i + 0x1D)
    if icon == 0:
        return False
    item, = _struct.unpack_from("<I", data, i + 0x15)
    if item == 0:
        return False
    return True


class WeaponAddresses:
    """Resolves all weapon field addresses from a single base (start_object).

    All offsets were derived from Shock Rocket (most complete weapon) and hold for every weapon:
      title            = base + 0x0D
      item             = base + 0x15
      menu_icon        = base + 0x1D
      mod_icon_one     = base + 0x21
      mod_icon_two     = base + 0x25
      mod_icon_three   = base + 0x29
      level            = base + 0x2D
      ammo             = base + 0x31
      experience       = base + 0x35
      mod_slot_one     = base + 0x3D  (uint8 boolean)
      mod_slot_two     = base + 0x3E  (uint8 boolean)
      mod_slot_three   = base + 0x3F  (uint8 boolean)
      unlocked         = base + 0x45  (uint8 boolean)
    """

    _OFFSETS: dict[str, int] = {
        "title":          0x0D,
        "item":           0x15,
        "menu_icon":      0x1D,
        "mod_icon_one":   0x21,
        "mod_icon_two":   0x25,
        "mod_icon_three": 0x29,
        "level":          0x2D,
        "ammo":           0x31,
        "experience":     0x35,
        "mod_slot_one":   0x3D,
        "mod_slot_two":   0x3E,
        "mod_slot_three": 0x3F,
        "unlocked":       0x45,
    }

    _BYTE_FIELDS: frozenset[str] = frozenset({"mod_slot_one", "mod_slot_two", "mod_slot_three", "unlocked"})

    def __init__(self, base: int) -> None:
        self.base = base
        for name, offset in self._OFFSETS.items():
            setattr(self, name, base + offset)

    def fields(self) -> list[str]:
        return list(self._OFFSETS)

    def is_byte(self, field: str) -> bool:
        return field in self._BYTE_FIELDS

    def __repr__(self) -> str:
        fields = "\n".join(
            f"  {name} = 0x{getattr(self, name):08X}"
            for name in self._OFFSETS
        )
        return f"WeaponAddresses(base=0x{self.base:08X})\n{fields}"


class GadgetAddresses:
    """Resolves gadget addresses from a single base (start_object).

    Gadgets share the same struct layout as weapons but only use two fields:
      icon     = base + 0x1D
      unlocked = base + 0x45  (uint8 boolean)
    """

    _OFFSETS: dict[str, int] = {
        "icon":     0x1D,
        "unlocked": 0x45,
    }

    _BYTE_FIELDS: frozenset[str] = frozenset({"unlocked"})

    def __init__(self, base: int) -> None:
        self.base = base
        for name, offset in self._OFFSETS.items():
            setattr(self, name, base + offset)

    def fields(self) -> list[str]:
        return list(self._OFFSETS)

    def is_byte(self, field: str) -> bool:
        return field in self._BYTE_FIELDS

    def __repr__(self) -> str:
        fields = "\n".join(
            f"  {name} = 0x{getattr(self, name):08X}"
            for name in self._OFFSETS
        )
        return f"GadgetAddresses(base=0x{self.base:08X})\n{fields}"


WEAPON_ORDER: list[str | None] = [
    "lacerator",        # slot  0
    "concussion_gun",   # slot  1
    "acid_bomb_glove",  # slot  2
    "agents_of_doom",   # slot  3
    "bee_mine_glove",   # slot  4
    "static_barrier",   # slot  5
    "shock_rocket",     # slot  6
    "sniper_mine",      # slot  7
    "scorcher",         # slot  8
    "laser_tracer",     # slot  9
    "suck_cannon",      # slot 10
    "mootator",         # slot 11
    None,               # slot 12  gap
    "ryno",             # slot 13
]

GADGET_ORDER: list[str | None] = [
    "hypershot",        # slot 0
    "sprout_o_matic",   # slot 1
    "polarizer",        # slot 2
    "pda",              # slot 3
    "shrink_ray",       # slot 4
    "bolt_grabber",     # slot 5
    None,               # slot 6  gap
    "map_o_matic",      # slot 7
    "box_breaker",      # slot 8
]


def build_weapons(array_base: int) -> tuple[dict[str, WeaponAddresses], dict[str, GadgetAddresses]]:
    weapons: dict[str, WeaponAddresses] = {}
    for i, name in enumerate(WEAPON_ORDER):
        if name is not None:
            weapons[name] = WeaponAddresses(array_base + i * WEAPON_STRUCT_SIZE)

    gadget_base = array_base + len(WEAPON_ORDER) * WEAPON_STRUCT_SIZE
    gadgets: dict[str, GadgetAddresses] = {}
    for i, name in enumerate(GADGET_ORDER):
        if name is not None:
            gadgets[name] = GadgetAddresses(gadget_base + i * WEAPON_STRUCT_SIZE)

    return weapons, gadgets
