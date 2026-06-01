from dataclasses import dataclass


@dataclass(frozen=True)
class TitaniumBolt:
    planet_id: int  # used with delta for unambiguous detection
    bit:       int  # bit position in the pickup int64
    region:    str  # AP region name

    @property
    def delta(self) -> int:
        return 1 << self.bit


TITANIUM_BOLTS: dict[str, TitaniumBolt] = {
    "Pokitaru Above Zipline (TB)":                      TitaniumBolt(0x01,  0, "Pokitaru"),
    "Pokitaru Behind Hut (TB)":                         TitaniumBolt(0x01,  1, "Pokitaru"),
    "Ryllus Down The Cliff (TB)":                       TitaniumBolt(0x02,  4, "Ryllus"),
    "Ryllus After the Wall (TB)":                       TitaniumBolt(0x02,  5, "Ryllus"),
    "Kalidon Behind The Ship (TB)":                     TitaniumBolt(0x03,  8, "Kalidon"),
    "Kalidon Side of Mechanoid Factory (TB)":           TitaniumBolt(0x03, 10, "Kalidon"),
    "Kalidon Grav-Ramps (TB)":                          TitaniumBolt(0x03, 11, "Kalidon"),
    "Metalis Behind the Polarized Door (TB)":           TitaniumBolt(0x04, 12, "Metalis"),
    "Dreamtime Jump Across three moving parasols (TB)": TitaniumBolt(0x05, 16, "Dreamtime"),
    "Dreamtime To the left of Ratchets Garage (TB)":   TitaniumBolt(0x05, 17, "Dreamtime"),
    "Dreamtime Apparition of the Scuttle Crab (TB)":   TitaniumBolt(0x05, 18, "Dreamtime"),
    "Outpost Omega Near the Entrance to DreamTime (TB)":TitaniumBolt(0x06, 20, "Outpost Omega"),
    "Challax Beside The Ultra Mech Pad (TB)":           TitaniumBolt(0x07, 24, "Challax"),
    "Challax Hidden Room (TB)":                         TitaniumBolt(0x07, 25, "Challax"),
    "Challax Mimic Plant Lob (TB)":                     TitaniumBolt(0x07, 26, "Challax"),
    "Dayni Moon Planting at the Barnyard (TB)":         TitaniumBolt(0x08, 28, "Dayni Moon"),
    "Dayni Moon Bounce on the Blue mimic (TB)":         TitaniumBolt(0x08, 29, "Dayni Moon"),
    "Inside Clank Walk behind the ladder (TB)":         TitaniumBolt(0x09, 32, "Inside Clank"),
    "Inside Clank Wall jumping Technomite (TB)":        TitaniumBolt(0x09, 33, "Inside Clank"),
    "Quodrona Ratchet Clones and Dummies (TB)":         TitaniumBolt(0x0A, 36, "Quodrona"),
}

# (planet_id, delta) → location name — used by the client for unambiguous detection
BOLT_BY_PLANET_AND_DELTA: dict[tuple[int, int], str] = {
    (bolt.planet_id, bolt.delta): name
    for name, bolt in TITANIUM_BOLTS.items()
}
