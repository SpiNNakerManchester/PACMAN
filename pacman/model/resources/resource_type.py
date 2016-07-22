from enum.enum import Enum


class ResourceType(Enum):
    """ A type of continuous resource available on a SpiNNaker machine
    """
    CPU_CYCLES = (1, "Number of CPU cycles for execution")
    N_CORES = (2, "Number of cores")
    SDRAM = (3, "Amount of SDRAM in bytes")
    DTCM = (4, "Amount of DTCM in bytes")
    SRAM = (5, "Amount of System RAM in bytes")

    def __new__(cls, value, doc=""):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.__doc__ = doc
        return obj

    def __init__(self, value, doc=""):
        self._value_ = value
        self.__doc__ = doc
