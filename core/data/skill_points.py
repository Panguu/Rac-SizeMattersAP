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
    "Skill Point Train Faster":                  SkillPoint(0x01,  0, "Pokitaru"),
    "Skill Point Dont Rock The Boat":            SkillPoint(0x01,  1, "Pokitaru"),
    "Skill Point Do Cows Get Crabby":            SkillPoint(0x01,  2, "Pokitaru"),
    # Ryllus
    "Skill Point Bury The Pygmies":              SkillPoint(0x02,  4, "Ryllus"),
    "Skill Point Lights Camera Action":          SkillPoint(0x02,  5, "Ryllus"),
    "Skill Point Ship It":                       SkillPoint(0x02,  6, "Ryllus"),
    # Kalidon
    "Skill Point Explosive Ordnance Disposal":   SkillPoint(0x03,  8, "Kalidon"),
    "Skill Point Super Lombax":                  SkillPoint(0x03,  9, "Kalidon"),
    "Skill Point Be A Cool Skyboarder":          SkillPoint(0x03, 10, "Kalidon"),
    # Metalis
    "Skill Point Shutout":                       SkillPoint(0x04, 12, "Metalis"),
    "Skill Point Terror of the Skies":           SkillPoint(0x04, 13, "Metalis"),
    "Skill Point Ultimate Gladiator":            SkillPoint(0x04, 14, "Metalis"),
    # Dreamtime
    "Skill Point Friends Dont Hurt Friends":     SkillPoint(0x05, 16, "Dreamtime"),
    "Skill Point Night Terrors":                 SkillPoint(0x05, 17, "Dreamtime"),
    # Outpost Omega
    "Be An Awesome Skyboarder":                  SkillPoint(0x06, 20, "Outpost Omega"),
    # Challax
    # "Skill Point Take Them Down A Shock": SkillPoint(0x07, 24, "Challax")
    # Excluded: only one opportunity to complete this in the whole game (bit 24).
    "Skill Point High Tech Weapons Master":      SkillPoint(0x07, 25, "Challax"),
    "Skill Point No More Varmints":              SkillPoint(0x07, 26, "Challax"),
    # Dayni Moon
    "Skill Point Ultimate Gladiator Dayni Moon": SkillPoint(0x08, 28, "Dayni Moon"),
    "Skill Point Wool Protest":                  SkillPoint(0x08, 29, "Dayni Moon"),
    "Skill Point Bouncy Bouncy Bouncy":          SkillPoint(0x08, 30, "Dayni Moon"),
    # Inside Clank
    "Skill Point Not The Shock of Me Now":       SkillPoint(0x09, 32, "Inside Clank"),
    "Skill Point Ratchet Just Ratchet":          SkillPoint(0x09, 33, "Inside Clank"),
    # Quodrona
    "Skill Point Elite Annihilation":            SkillPoint(0x0A, 36, "Quodrona"),
    "Skill Point Storm The Front":               SkillPoint(0x0A, 37, "Quodrona"),
}

CHALLENGE_SKILL_POINTS: frozenset[str] = frozenset({
    "Skill Point Be A Cool Skyboarder",
    "Skill Point Shutout",
    "Skill Point Terror of the Skies",
    "Skill Point Ultimate Gladiator",
    "Skill Point Ultimate Gladiator Dayni Moon",
    "Be An Awesome Skyboarder",
    "Skill Point No More Varmints",
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
