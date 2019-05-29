"""Data structures for the definition of SpiNNaker routing tables.

Based on https://github.com/project-rig/rig/blob/master/rig/routing_table/entries.py
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
        """Get an easily readable representation of the routing table entry.

        Representations take the form::

            XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX -> N NE ...

        For example::

            >>> rte = RoutingTableEntry({Routes.core(5)}, 0b1010, 0xf)
            >>> print(str(rte))
            XXXXXXXXXXXXXXXXXXXXXXXXXXXX1010 -> 5

        If source directions are provided then the source links are also
        indicated in the string. For example, if packets come from the South
        link:

            >>> rte = RoutingTableEntry({Routes.core(2)},
            ...                         0x00010000,
            ...                         0xffff0000,
            ...                         {Routes.south})
            >>> print(str(rte))
            S -> 0000000000000001XXXXXXXXXXXXXXXX -> 2
        """
        # Build the representation of the key and mask
        keymask = "".join(
            ("1" if self.key & bit else "0") if self.mask & bit else
            ("!" if self.key & bit else "X") for bit in
            (1 << (31 - i) for i in range(32))
        )

        # Get the routes strings
        route = " ".join(r.initial for r in sorted(self.route))

        # If no sources then don't display sources
        return "{} -> {} -> {}".format(keymask, route, self.defaultable)
