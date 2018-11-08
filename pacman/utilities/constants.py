from enum import Enum

DEFAULT_MASK = 0xfffff800  # DEFAULT LOCATION FOR THE APP MASK
BITS_IN_KEY = 32

CORES_PER_VIRTUAL_CHIP = 128

EDGES = Enum(
    value="EDGES",
    names=[("EAST", 0),
           ("NORTH_EAST", 1),
           ("NORTH", 2),
           ("WEST", 3),
           ("SOUTH_WEST", 4),
           ("SOUTH", 5)])
