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


# Bit layout — groups of 3 per 4-bit nibble, one bit gap between planets:
#
#  First word  (bits  0–31): Pokitaru → Outpost Omega
#   Pokitaru  (3): bits  0,  1,  2
#   Ryllus    (3): bits  4,  5,  6
#   Kalidon   (3): bits  8,  9, 10
#   Metalis   (3): bits 12, 13, 14
#   Dreamtime (2): bits 16, 17
#   Outpost Ω (1): bit  20
#
#  Second word (bits 32–63): Challax → Quodrona
#   Challax    (3): bits 32, 33, 34
#   Dayni Moon (3): bits 36, 37, 38
#   Inside Clank(2):bits 40, 41
#   Quodrona   (2): bits 44, 45

SKILL_POINTS: dict[str, SkillPoint] = {
    # Pokitaru — confirmed
    "Skill Point Train Faster":                  SkillPoint(0x01,  0, "Pokitaru"),
    "Skill Point Dont Rock The Boat":            SkillPoint(0x01,  1, "Pokitaru"),
    "Skill Point Do Cows Get Crabby":            SkillPoint(0x01,  2, "Pokitaru"),
    # Ryllus — bits 5 & 6 confirmed; bit 4 estimated
    "Skill Point Bury The Pygmies":              SkillPoint(0x02,  4, "Ryllus"),       # estimated
    "Skill Point Lights Camera Action":          SkillPoint(0x02,  5, "Ryllus"),
    "Skill Point Ship It":                       SkillPoint(0x02,  6, "Ryllus"),
    # Kalidon — estimated
    "Skill Point Explosive Ordnance Disposal":   SkillPoint(0x03,  8, "Kalidon"),      # estimated
    "Skill Point Super Lombax":                  SkillPoint(0x03,  9, "Kalidon"),      # estimated
    "Skill Point Be A Cool Skyboarder":          SkillPoint(0x03, 10, "Kalidon"),      # estimated
    # Metalis — estimated
    "Skill Point Shutout":                       SkillPoint(0x04, 12, "Metalis"),      # estimated
    "Skill Point Terror of the Skies":           SkillPoint(0x04, 13, "Metalis"),      # estimated
    "Skill Point Ultimate Gladiator":            SkillPoint(0x04, 14, "Metalis"),      # estimated
    # Dreamtime — estimated
    "Skill Point Friends Dont Hurt Friends":     SkillPoint(0x05, 16, "Dreamtime"),    # estimated
    "Skill Point Night Terrors":                 SkillPoint(0x05, 17, "Dreamtime"),    # estimated
    # Outpost Omega — estimated
    "Be An Awesome Skyboarder":                  SkillPoint(0x06, 20, "Outpost Omega"),# estimated
    # Challax — estimated
    "Skill Point Take Them Down A Shock":        SkillPoint(0x07, 32, "Challax"),      # estimated
    "Skill Point High Tech Weapons Master":      SkillPoint(0x07, 33, "Challax"),      # estimated
    "Skill Point No More Varmints":              SkillPoint(0x07, 34, "Challax"),      # estimated
    # Dayni Moon — estimated
    "Skill Point Ultimate Gladiator Dayni Moon": SkillPoint(0x08, 36, "Dayni Moon"),   # estimated
    "Skill Point Wool Protest":                  SkillPoint(0x08, 37, "Dayni Moon"),   # estimated
    "Skill Point Bouncy Bouncy Bouncy":          SkillPoint(0x08, 38, "Dayni Moon"),   # estimated
    # Inside Clank — estimated
    "Skill Point Not The Shock of Me Now":       SkillPoint(0x09, 40, "Inside Clank"), # estimated
    "Skill Point Ratchet Just Ratchet":          SkillPoint(0x09, 41, "Inside Clank"), # estimated
    # Quodrona — estimated
    "Skill Point Elite Annihilation":            SkillPoint(0x0A, 44, "Quodrona"),     # estimated
    "Skill Point Storm The Front":               SkillPoint(0x0A, 45, "Quodrona"),     # estimated
}

# (planet_id, mask) → location name — mirrors BOLT_BY_PLANET_AND_DELTA
SKILL_POINT_BY_PLANET_AND_MASK: dict[tuple[int, int], str] = {
    (sp.planet_id, sp.mask): name
    for name, sp in SKILL_POINTS.items()
}

# Flat mask lookup used by the client (bits are globally unique so planet not needed for detection)
LOCATION_SKILL_POINTS: dict[str, int] = {
    name: sp.mask for name, sp in SKILL_POINTS.items()
}
