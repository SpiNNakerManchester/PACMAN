from enum import Enum


class EdgeTrafficType(Enum):
    """ Indicates the traffic type of an Edge in a graph
    """

    MULTICAST = 1
    FIXED_ROUTE = 2
