class TitaniumBoltAddresses:
    """Resolves titanium bolt field addresses from a single base address.

    Layout (identical on PSP and PS2):
      +0x00  pickup  — increments each time a bolt is picked up
      +0x05  total   — cumulative bolt count
    """

    def __init__(self, base: int) -> None:
        self.base   = base
        self.pickup = base + 0x00
        self.total  = base + 0x05
