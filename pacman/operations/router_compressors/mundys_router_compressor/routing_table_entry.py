"""Data structures for the definition of SpiNNaker routing tables.

Based on
https://github.com/project-rig/rig/blob/master/rig/routing_table/entries.py
"""


class RoutingTableEntry(object):
    """representing a single routing entry in a SpiNNaker routing table.

    Parameters
    ----------
    route : {:py:class:`~.Routes`, ...}
        The set of destinations a packet should be routed to where each element
        in the set is a value from the enumeration
        :py:class:`~rig.routing_table.Routes`.
    key : int
        32-bit unsigned integer routing key to match after applying the mask.
    mask : int
        32-bit unsigned integer mask to apply to keys of packets arriving at
        the router.
    """

    _slots__ = ["route", "key", "mask", "defaultable"]

    def __init__(self, route, key, mask, defaultable):
        self.route = route
        self.key = key
        self.mask = mask
        self.defaultable = defaultable

    def __str__(self):
        # If no sources then don't display sources
        return "key:{} mask:{} route:{} defaultable:{}".format(
            self.key, self.mask, self.route, self.defaultable)
