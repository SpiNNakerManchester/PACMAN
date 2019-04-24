"""Datastructures for representing the resources available in a machine when
performing placement, allocation and routing.
"""

from pacman.myrig.links import Links

import sentinel


Cores = sentinel.create("Cores")
"""Resource identifier for (monitor and application) processor cores.

Note that this identifier does not trigger any kind of special-case behaviour
in library functions. Users are free to define their own alternatives.

In early versions of Rig this object was called ``rig.machine.Cores``.
"""


SDRAM = sentinel.create("SDRAM")
"""Resource identifier for shared off-die SDRAM (in bytes).

Note that this identifier does not trigger any kind of special-case behaviour
in library functions. Users are free to define their own alternatives.

.. note::

    In early versions of Rig this object was called ``rig.machine.SDRAM``.
"""


SRAM = sentinel.create("SRAM")
"""Resource identifier for shared on-die SRAM (in bytes).

Note that this identifier does not trigger any kind of special-case behaviour
in library functions. Users are free to define their own alternatives.

.. note::

    In early versions of Rig this object was called ``rig.machine.SRAM``.
"""


class Machine(object):
    """Defines the resources available in a SpiNNaker machine.

    This datastructure makes the assumption that in most systems almost
    everything is uniform and working.

    This data-structure intends to be completely transparent. Its contents are
    described below. A number of utility methods are available but should be
    considered just that: utilities.

    .. note::

        In early versions of Rig this object was called
        ``rig.machine.Machine``.

    Attributes
    ----------
    width : int
        The width of the system in chips: chips will thus have x-coordinates
        between 0 and width-1 inclusive.
    height : int
        The height of the system in chips: chips will thus have y-coordinates
        between 0 and height-1 inclusive.
    chip_resources : {resource_key: requirement, ...}
        The resources available on chips (unless otherwise stated in
        `chip_resource_exceptions). `resource_key` must be some unique
        identifying object for a given resource. `requirement` must be a
        positive numerical value. For example: `{Cores: 17, SDRAM:
        128*1024*1024}` would indicate 17 cores and 128 MBytes of SDRAM.
    chip_resource_exceptions : {(x,y): resources, ...}
        If any chip's resources differ from those specified in
        `chip_resources`, an entry in this dictionary with the key being the
        chip's coordinates as a tuple `(x, y)` and `resources` being a
        dictionary of the same format as `chip_resources`. Note that every
        exception must specify exactly the same set of keys as
        `chip_resources`.
    dead_chips : set
        A set of `(x,y)` tuples enumerating all chips which completely
        unavailable. Links leaving a dead chip are implicitly marked as dead.
    dead_links : set
        A set `(x,y,link)` where `x` and `y` are a chip's coordinates and
        `link` is a value from the Enum :py:class:`~rig.links.Links`. Note
        that links have two directions and both should be defined if a link is
        dead in both directions (the typical case).
    """

    def __init__(self, width, height,
                 chip_resources={Cores: 18, SDRAM: 128*1024*1024,
                                 SRAM: 32*1024},
                 chip_resource_exceptions={}, dead_chips=set(),
                 dead_links=set()):
        """Defines the resources available within a SpiNNaker system.

        Parameters
        ----------
        width : int
        height : int
        chip_resources : {resource_key: requirement, ...}
        chip_resource_exceptions : {(x,y): resources, ...}
        dead_chips : set([(x,y,p), ...])
        dead_links : set([(x,y,link), ...])
        """
        self.width = width
        self.height = height

        self.chip_resources = chip_resources.copy()
        self.chip_resource_exceptions = chip_resource_exceptions.copy()

        self.dead_chips = dead_chips.copy()
        self.dead_links = dead_links.copy()

    def copy(self):
        """Produce a copy of this datastructure."""
        return Machine(
            self.width, self.height,
            self.chip_resources, self.chip_resource_exceptions,
            self.dead_chips, self.dead_links)

    def __eq__(self, other):
        """Test whether this Machine describes the same machine as another."""
        return (self.width == other.width and
                self.height == other.height and
                self.chip_resources == other.chip_resources and
                all(self[chip] == other[chip]
                    for chip in self.chip_resource_exceptions) and
                all(self[chip] == other[chip]
                    for chip in other.chip_resource_exceptions) and
                self.dead_chips == other.dead_chips and
                self.dead_links == other.dead_links)

    def __ne__(self, other):
        return not (self == other)

    def issubset(self, other):
        """Test whether the resources available in this machine description are
        a (non-strict) subset of those available in another machine.

        .. note::

            This test being False does not imply that the this machine is
            a superset of the other machine; machines may have disjoint
            resources.
        """
        return (set(self).issubset(set(other)) and
                set(self.iter_links()).issubset(set(other.iter_links())) and
                all(set(self[chip]).issubset(other[chip]) and
                    all(self[chip][r] <= other[chip][r]
                        for r in self[chip])
                    for chip in self))

    def __contains__(self, chip_or_link):
        """Test if a given chip or link is present and alive.

        Parameters
        ----------
        chip_or_link : tuple
            If of the form `(x, y, link)`, checks a link. If of the form `(x,
            y)`, checks a core.
        """
        if len(chip_or_link) == 2:
            x, y = chip_or_link
            return 0 <= x < self.width and 0 <= y < self.height \
                and (x, y) not in self.dead_chips
        elif len(chip_or_link) == 3:
            x, y, link = chip_or_link
            return (x, y) in self and (x, y, link) not in self.dead_links
        else:
            raise ValueError("Expect either (x, y) or (x, y, link).")

    def __getitem__(self, xy):
        """Get the resources available to a given chip.

        Raises
        ------
        IndexError
            If the given chip is dead or not within the bounds of the system.
        """
        if xy not in self:
            raise IndexError("{} is not part of the machine.".format(repr(xy)))

        return self.chip_resource_exceptions.get(xy, self.chip_resources)

    def __setitem__(self, xy, resources):
        """Specify the resources available to a given chip.

        Raises
        ------
        IndexError
            If the given chip is dead or not within the bounds of the system.
        """
        if xy not in self:
            raise IndexError("{} is not part of the machine.".format(repr(xy)))

        self.chip_resource_exceptions[xy] = resources

    def __iter__(self):
        """Iterate over the working chips in the machine.

        Generates a series of (x, y) tuples.
        """
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) in self:
                    yield (x, y)

    def iter_links(self):
        """An iterator over the working links in the machine.

        Generates a series of (x, y, link) tuples.
        """
        for x in range(self.width):
            for y in range(self.height):
                for link in Links:
                    if (x, y, link) in self:
                        yield (x, y, link)

    def has_wrap_around_links(self, minimum_working=0.9):
        """Test if a machine has wrap-around connections installed.

        Since the Machine object does not explicitly define whether a machine
        has wrap-around links they must be tested for directly. This test
        performs a "fuzzy" test on the number of wrap-around links which are
        working to determine if wrap-around links are really present.

        Parameters
        ----------
        minimum_working : 0.0 <= float <= 1.0
            The minimum proportion of all wrap-around links which must be
            working for this function to return True.

        Returns
        -------
        bool
            True if the system has wrap-around links, False if not.
        """
        working = 0
        for x in range(self.width):
            if (x, 0, Links.south) in self:
                working += 1
            if (x, self.height - 1, Links.north) in self:
                working += 1
            if (x, 0, Links.south_west) in self:
                working += 1
            if (x, self.height - 1, Links.north_east) in self:
                working += 1

        for y in range(self.height):
            if (0, y, Links.west) in self:
                working += 1
            if (self.width - 1, y, Links.east) in self:
                working += 1

            # Don't re-count links counted when scanning the x-axis
            if y != 0 and (0, y, Links.south_west) in self:
                working += 1
            if (y != self.height - 1 and
                    (self.width - 1, y, Links.north_east) in self):
                working += 1

        total = (4 * self.width) + (4 * self.height) - 2

        return (float(working) / float(total)) >= minimum_working
