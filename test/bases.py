from test.bases import WorldTestBase


class RACSizeMatterTestBase(WorldTestBase):
    game = "Ratchet & Clank: Size Matters"


# Shared item sets used across test files
ANY_PROJECTILE  = "Lacerator"
RYLLUS_ITEMS    = [ANY_PROJECTILE, "Hypershot", "Sprout-O-Matic"]
KALIDON_ITEMS   = RYLLUS_ITEMS
METALIS_ITEMS   = [*KALIDON_ITEMS, "Shrink Ray"]
CHALLAX_ITEMS   = [*METALIS_ITEMS, "Polarizer"]
ALL_PLANETS     = CHALLAX_ITEMS
