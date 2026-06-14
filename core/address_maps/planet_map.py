from __future__ import annotations

from ...interface_orchestrator.structs.address_map import AddressMap
from ..data.addresses import (
    MENU_ADDR_BY_PLANET_ID,
    PLAYER_ADDRS,
    PRELOAD_MENU_ADDR_BY_PLANET_ID,
    WEAPON_ARRAY_BASE_BY_PLANET,
)
from ..data.display_text_box import TextBoxDisplayAddrs
from ..data.weapons import (
    build_weapons,
)
from ..structs.display_text import make_countdown_cls, make_vendor_visibility_cls
from ..structs.menu import make_menu_cls, make_preload_menu_cls
from ..structs.player import make_player_movement_cls
from ..structs.weapon import make_gadget_struct_cls, make_weapon_struct_cls

_TEXTBOX_BY_PLANET = {tb.planet_id: tb for tb in TextBoxDisplayAddrs}

_PLANET_ID_TO_NAME: dict[int, str] = {
    0x01: "Pokitaru",
    0x02: "Ryllus",
    0x03: "Kalidon",
    0x04: "Metalis",
    0x05: "Dreamtime",
    0x06: "OutpostOmega",
    0x07: "Challax",
    0x08: "DayniMoon",
    0x09: "InsideClank",
    0x0A: "Quodrona",
    0x17: "OutpostOmega2",
}

def build_planet_address_map(planet_id: int) -> AddressMap:
    planet_name = _PLANET_ID_TO_NAME.get(planet_id, f"Planet{planet_id:02X}")
    address_map = AddressMap(interface_id=f"planet_{planet_id:#04x}")

    if planet_id in PLAYER_ADDRS:
        movement_addr, _health_addr = PLAYER_ADDRS[planet_id]
        address_map.register(make_player_movement_cls(planet_name, movement_addr))

    if planet_id in MENU_ADDR_BY_PLANET_ID:
        address_map.register(make_menu_cls(planet_name, MENU_ADDR_BY_PLANET_ID[planet_id]))
    if planet_id in PRELOAD_MENU_ADDR_BY_PLANET_ID:
        address_map.register(
            make_preload_menu_cls(planet_name, PRELOAD_MENU_ADDR_BY_PLANET_ID[planet_id])
        )

    tb = _TEXTBOX_BY_PLANET.get(planet_id)
    if tb is not None:
        address_map.register(make_countdown_cls(planet_name, tb.countdown_timer))
        address_map.register(make_vendor_visibility_cls(planet_name, tb.message_str_pointer))

    if planet_id in WEAPON_ARRAY_BASE_BY_PLANET:
        array_base = WEAPON_ARRAY_BASE_BY_PLANET[planet_id]
        weapon_addrs, gadget_addrs = build_weapons(array_base)
        for name, addrs in weapon_addrs.items():
            address_map.register(make_weapon_struct_cls(name, addrs.base))
        for name, addrs in gadget_addrs.items():
            address_map.register(make_gadget_struct_cls(name, addrs.base))

    return address_map

def build_combined_address_map(planet_id: int, global_map: AddressMap) -> AddressMap:
    combined = AddressMap(interface_id=f"combined_{planet_id:#04x}")
    for struct_cls in global_map.structs():
        combined.register(struct_cls)
    for struct_cls in build_planet_address_map(planet_id).structs():
        combined.register(struct_cls)
    return combined
