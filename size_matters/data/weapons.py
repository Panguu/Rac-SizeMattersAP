from ..weapons import WeaponAddresses, GadgetAddresses, WEAPON_STRUCT_SIZE

WEAPON_ORDER: list[str | None] = [
    "lacerator",        # slot  0
    "concussion_gun",   # slot  1
    "acid_bomb_glove",  # slot  2
    "agents_of_doom",   # slot  3
    "bee_mine_glove",   # slot  4
    "static_barier",    # slot  5
    "shock_rocket",     # slot  6
    "sniper_mine",      # slot  7
    "scorchet",         # slot  8
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
