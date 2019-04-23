"""Data structures for the definition of SpiNNaker routing tables.
"""

from enum import IntEnum

from collections import namedtuple


class RoutingTableEntry(namedtuple("RoutingTableEntry",
                                   "route key mask sources")):
    """Named tuple representing a single routing entry in a SpiNNaker routing
    table.

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
    sources : {:py:class:`~.Routes`, ...}
        Links on which a packet may enter the router before taking this route.
        If the source directions are unknown ``{None}`` should be used (the
        default).
    """
    def __new__(cls, route, key, mask, sources={None}):
        return super(RoutingTableEntry, cls).__new__(
            cls, frozenset(route), key, mask, set(sources)
        )

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

        if not self.sources or self.sources == {None}:
            # If no sources then don't display sources
            return "{} -> {}".format(keymask, route)
        else:
            # Otherwise get the sources
            source = " ".join(s.initial for s in
                              sorted(self.sources - {None}))
            return "{} -> {} -> {}".format(source, keymask, route)


class Routes(IntEnum):
    """Enumeration of routes which a SpiNNaker packet can take after arriving
    at a router.

    Note that the integer values assigned are chosen to match the numbers used
    to identify routes in the low-level software API and hardware registers.

    Note that you can directly cast from a :py:class:`rig.links.Links` to a
    Routes value.
    """

    @classmethod
    def core(cls, num):
        """Get the :py:class:`.Routes` for the numbered core.

        Raises
        ------
        ValueError
            If the core number isn't in the range 0-17 inclusive.
        """
        if not (0 <= num <= 17):
            raise ValueError("Cores are numbered from 0 to 17")
        return cls(6 + num)

    east = 0
    north_east = 1
    north = 2
    west = 3
    south_west = 4
    south = 5

    core_monitor = 6
    core_1 = 7
    core_2 = 8
    core_3 = 9
    core_4 = 10
    core_5 = 11
    core_6 = 12
    core_7 = 13
    core_8 = 14
    core_9 = 15
    core_10 = 16
    core_11 = 17
    core_12 = 18
    core_13 = 19
    core_14 = 20
    core_15 = 21
    core_16 = 22
    core_17 = 23

    @property
    def is_link(self):
        """True iff a Routes object represents a chip to chip link."""
        return self < 6

    @property
    def is_core(self):
        """True iff a Routes object represents a route to a core."""
        return not self.is_link

    @property
    def core_num(self):
        """Get the core number being routed to.

        Raises
        ------
        ValueError
            If the route is not to a core.
        """
        if self.is_core:
            return self - 6
        else:
            raise ValueError("{} is not a core".format(repr(self)))

    @property
    def opposite(self):
        """Get the route going in the opposing direction.

        Raises
        ------
        ValueError
            If the Route is not a link.
        """
        if not self.is_link:
            raise ValueError("{} does not have an opposite".format(self))

        return Routes((self + 3) % 6)

    @property
    def initial(self):
        """Get a shorter string representation of the Route."""
        links_strs = {
            Routes.east: "E",
            Routes.north_east: "NE",
            Routes.north: "N",
            Routes.west: "W",
            Routes.south_west: "SW",
            Routes.south: "S",
        }

        if self.is_link:
            return links_strs[self]
        else:
            return str(self.core_num)
