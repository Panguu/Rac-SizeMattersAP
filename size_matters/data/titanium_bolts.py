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
    "Pokitaru Titanium Bolt Above Zipline":                      TitaniumBolt(0x01,  0, "Pokitaru"),       # estimated
    "Pokitaru Titanium Bolt Behind Hut":                         TitaniumBolt(0x01,  1, "Pokitaru"),       # estimated
    "Ryllus Titanium Bolt Down The Cliff":                       TitaniumBolt(0x02,  4, "Ryllus"),
    "Ryllus Titanium Bolt After the Wall":                       TitaniumBolt(0x02,  5, "Ryllus"),
    "Kalidon Titanium Bolt Behind The Ship":                     TitaniumBolt(0x03,  8, "Kalidon"),
    "Kalidon Titanium Bolt Side of Mechanoid Factory":           TitaniumBolt(0x03, 10, "Kalidon"),
    "Kalidon Titanium Bolt Grav-Ramps":                          TitaniumBolt(0x03, 11, "Kalidon"),        # estimated
    "Metalis Titanium Bolt Behind the Polarized Door":           TitaniumBolt(0x04, 12, "Metalis"),
    "Dreamtime Titanium Bolt Jump Across three moving parasols": TitaniumBolt(0x05, 16, "Dreamtime"),      # estimated
    "Dreamtime Titanium Bolt To the left of Ratchets Garage":   TitaniumBolt(0x05, 17, "Dreamtime"),
    "Dreamtime Titanium Bolt Apparition of the Scuttle Crab":   TitaniumBolt(0x05, 18, "Dreamtime"),      # estimated
    "Outpost Omega Titanium Bolt Near the Entrance to DreamTime":TitaniumBolt(0x06, 20, "Outpost Omega"),
    "Challax Titanium Bolt Beside The Ultra Mech Pad":           TitaniumBolt(0x07, 24, "Challax"),
    "Challax Titanium Bolt Hidden Room":                         TitaniumBolt(0x07, 25, "Challax"),
    "Challax Titanium Bolt Mimic Plant Lob":                     TitaniumBolt(0x07, 26, "Challax"),
    "Dayni Moon Titanium Bolt Planting at the Barnyard":         TitaniumBolt(0x08, 28, "Dayni Moon"),
    "Dayni Moon Titanium Bolt Bounce on the Blue mimic":         TitaniumBolt(0x08, 29, "Dayni Moon"),
    "Inside Clank Titanium Bolt Walk behind the ladder":         TitaniumBolt(0x09, 32, "Inside Clank"),
    "Inside Clank Titanium Bolt Wall jumping Technomite":        TitaniumBolt(0x09, 33, "Inside Clank"),
    "Quodrona Titanium Bolt Ratchet Clones and Dummies":         TitaniumBolt(0x0A, 36, "Quodrona"),
}

# (planet_id, delta) → location name — used by the client for unambiguous detection
BOLT_BY_PLANET_AND_DELTA: dict[tuple[int, int], str] = {
    (bolt.planet_id, bolt.delta): name
    for name, bolt in TITANIUM_BOLTS.items()
}
