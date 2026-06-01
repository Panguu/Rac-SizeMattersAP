from enum import IntEnum


class PlayerState(IntEnum):
    Alive           = 0x00
    FishDeath       = 0x29
    FadeDeath      = 0x2A
    Electrocution  = 0x2B
    VoidDeath      = 0x2C
    UnknownDeath   = 0x2D
    SwimDeath      = 0x2E
    MysteriousDeath = 0x2F
    Pickup         = 0x43

    @staticmethod
    def is_dead(state: int) -> bool:
        return PlayerState.FishDeath <= state <= PlayerState.MysteriousDeath
