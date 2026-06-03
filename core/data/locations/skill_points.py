from dataclasses import dataclass

SKILL_POINT_ADDRESS = 0x21F4B437


@dataclass(frozen=True)
class SkillPoint:
    planet_id: int  # used with mask for detection context
    bit:       int
    region:    str

    @property
    def mask(self) -> int:
        return 1 << self.bit


# Confirmed bit layout (groups of 2-3, 4-bit spacing between planets):
#
#  Planet        Count  Bits
#  ──────────────────────────
#  Pokitaru        3     0,  1,  2
#  Ryllus          3     4,  5,  6
#  Kalidon         3     8,  9, 10
#  Metalis         3    12, 13, 14
#  Dreamtime       2    16, 17
#  Outpost Omega   1    20
#  Challax         3    24, 25, 26
#  Dayni Moon      3    28, 29, 30
#  Inside Clank    2    32, 33
#  Quodrona        2    36, 37

SKILL_POINTS: dict[str, SkillPoint] = {
    # Pokitaru
    "Train Faster (SP)":                  SkillPoint(0x01,  0, "Pokitaru"),
    "Dont Rock The Boat (SP)":            SkillPoint(0x01,  1, "Pokitaru"),
    "Do Cows Get Crabby (SP)":            SkillPoint(0x01,  2, "Pokitaru"),
    # Ryllus
    "Bury The Pygmies (SP)":              SkillPoint(0x02,  4, "Ryllus"),
    "Lights Camera Action (SP)":          SkillPoint(0x02,  5, "Ryllus"),
    "Ship It (SP)":                       SkillPoint(0x02,  6, "Ryllus"),
    # Kalidon
    "Explosive Ordnance Disposal (SP)":   SkillPoint(0x03,  8, "Kalidon"),
    "Super Lombax (SP)":                  SkillPoint(0x03,  9, "Kalidon"),
    "Be A Cool Skyboarder (SP)":          SkillPoint(0x03, 10, "Kalidon"),
    # Metalis
    "Shutout (SP)":                       SkillPoint(0x04, 12, "Metalis"),
    "Terror of the Skies (SP)":           SkillPoint(0x04, 13, "Metalis"),
    "Ultimate Gladiator (SP)":            SkillPoint(0x04, 14, "Metalis"),
    # Dreamtime
    "Friends Dont Hurt Friends (SP)":     SkillPoint(0x05, 16, "Dreamtime"),
    "Night Terrors (SP)":                 SkillPoint(0x05, 17, "Dreamtime"),
    # Outpost Omega
    "Be An Awesome Skyboarder (SC)":      SkillPoint(0x06, 20, "Outpost Omega"),
    # Challax
    # "Take Them Down A Shock (SP)": SkillPoint(0x07, 24, "Challax")
    # Excluded: only one opportunity to complete this in the whole game (bit 24).
    "High Tech Weapons Master (SP)":      SkillPoint(0x07, 25, "Challax"),
    "No More Varmints (SP)":              SkillPoint(0x07, 26, "Challax"),
    # Dayni Moon
    "Ultimate Gladiator Dayni Moon (SP)": SkillPoint(0x08, 28, "Dayni Moon"),
    "Wool Protest (SP)":                  SkillPoint(0x08, 29, "Dayni Moon"),
    "Bouncy Bouncy Bouncy (SP)":          SkillPoint(0x08, 30, "Dayni Moon"),
    # Inside Clank
    "Not The Shock of Me Now (SP)":       SkillPoint(0x09, 32, "Inside Clank"),
    "Ratchet Just Ratchet (SP)":          SkillPoint(0x09, 33, "Inside Clank"),
    # Quodrona
    "Elite Annihilation (SP)":            SkillPoint(0x0A, 36, "Quodrona"),
    "Storm The Front (SP)":               SkillPoint(0x0A, 37, "Quodrona"),
}

CHALLENGE_SKILL_POINTS: frozenset[str] = frozenset({
    "Be A Cool Skyboarder (SP)",
    "Shutout (SP)",
    "Terror of the Skies (SP)",
    "Ultimate Gladiator (SP)",
    "Ultimate Gladiator Dayni Moon (SP)",
    "Be An Awesome Skyboarder (SC)",
    "No More Varmints (SP)",
})

# (planet_id, mask) → location name — mirrors BOLT_BY_PLANET_AND_DELTA
SKILL_POINT_BY_PLANET_AND_MASK: dict[tuple[int, int], str] = {
    (sp.planet_id, sp.mask): name
    for name, sp in SKILL_POINTS.items()
}

# Flat mask lookup used by the client (bits are globally unique so planet not needed for detection)
LOCATION_SKILL_POINTS: dict[str, int] = {
    name: sp.mask for name, sp in SKILL_POINTS.items()
}
