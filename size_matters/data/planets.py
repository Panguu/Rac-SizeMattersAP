from __future__ import annotations
from dataclasses import dataclass
from .addresses import MENU_ADDR_BY_PLANET_ID


@dataclass(frozen=True)
class Planet:
    name:      str
    planet_id: int
    menu_addr: int | None = None


class Planets:
    POKITARU        = Planet("Pokitaru",              0x01, menu_addr=MENU_ADDR_BY_PLANET_ID[0x01])
    RYLLUS          = Planet("Ryllus",                0x02, menu_addr=MENU_ADDR_BY_PLANET_ID[0x02])
    KALIDON         = Planet("Kalidon",               0x03, menu_addr=MENU_ADDR_BY_PLANET_ID[0x03])
    METALIS         = Planet("Metalis",               0x04, menu_addr=MENU_ADDR_BY_PLANET_ID[0x04])
    DREAMTIME       = Planet("Dreamtime",             0x05, menu_addr=MENU_ADDR_BY_PLANET_ID[0x05])
    OUTPOST_OMEGA_1 = Planet("Outpost Omega 1",       0x06)
    CHALLAX         = Planet("Challax",               0x07, menu_addr=MENU_ADDR_BY_PLANET_ID[0x07])
    DAYNI_MOON      = Planet("Dayni Moon",            0x08, menu_addr=MENU_ADDR_BY_PLANET_ID[0x08])
    INSIDE_CLANK    = Planet("Inside Clank",          0x09)
    QUODRONA        = Planet("Quodrona",              0x0A, menu_addr=MENU_ADDR_BY_PLANET_ID[0x0A])
    GIANT_CLANK_META = Planet("Giant Clank (Metalis)", 0x0F)
    GIANT_CLANK_CHAL = Planet("Giant Clank (Challax)", 0x15)
    KALIDON_RACE    = Planet("Kalidon Race Track",    0x16)
    OUTPOST_OMEGA_2 = Planet("Outpost Omega 2",       0x17, menu_addr=MENU_ADDR_BY_PLANET_ID[0x17])


BY_ID: dict[int, Planet] = {
    p.planet_id: p
    for p in vars(Planets).values()
    if isinstance(p, Planet)
}
