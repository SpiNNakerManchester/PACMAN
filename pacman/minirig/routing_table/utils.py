from collections import defaultdict, namedtuple, OrderedDict

from pacman.operations.rig_algorithms.routing_table_entry import RoutingTableEntry
from pacman.minirig.routing_table.exceptions import MultisourceRouteError
from six import iteritems
import warnings


def routing_tree_to_tables(routes, net_keys):
    """Convert a set of
    :py:class:`~rig.place_and_route.routing_tree.RoutingTree` s into a per-chip
    set of routing tables.

    .. warning::
        A :py:exc:`rig.routing_table.MultisourceRouteError` will
        be raised if entries with identical keys and masks but with differing
        routes are generated. This is not a perfect test, entries which would
        otherwise collide are not spotted.

    .. warning::
        The routing trees provided are assumed to be correct and continuous
        (not missing any hops). If this is not the case, the output is
        undefined.

    .. note::
        If a routing tree has a terminating vertex whose route is set to None,
        that vertex is ignored.

    Parameters
    ----------
    routes : {net: :py:class:`~rig.place_and_route.routing_tree.RoutingTree`, \
              ...}
        The complete set of RoutingTrees representing all routes in the system.
        (Note: this is the same data structure produced by routers in the
        :py:mod:`~rig.place_and_route` module.)
    net_keys : {net: (key, mask), ...}
        The key and mask associated with each net.

    Returns
    -------
    {(x, y): [:py:class:`~rig.routing_table.RoutingTableEntry`, ...]
    """
    # Pairs of inbound and outbound routes.
    InOutPair = namedtuple("InOutPair", "ins, outs")

    # {(x, y): {(key, mask): _InOutPair}}
    route_sets = defaultdict(OrderedDict)

    for net, routing_tree in iteritems(routes):
        key, mask = net_keys[net]

        # The direction is the Links entry which describes the direction in
        # which we last moved to reach the node (or None for the root).
        for direction, (x, y), out_directions in routing_tree.traverse():
            # Determine the in_direction
            in_direction = direction
            if in_direction is not None:
                in_direction = direction.opposite

            # Add a routing entry
            if (key, mask) in route_sets[(x, y)]:
                # If there is an existing route set raise an error if the out
                # directions are not equivalent.
                if route_sets[(x, y)][(key, mask)].outs != out_directions:
                    raise MultisourceRouteError(key, mask, (x, y))

                # Otherwise, add the input directions as this represents a
                # merge of the routes.
                route_sets[(x, y)][(key, mask)].ins.add(in_direction)
            else:
                # Otherwise create a new route set
                route_sets[(x, y)][(key, mask)] = \
                    InOutPair({in_direction}, set(out_directions))

    # Construct the routing tables from the route sets
    routing_tables = defaultdict(list)
    for (x, y), routes in iteritems(route_sets):
        for (key, mask), route in iteritems(routes):
            # Add the route
            routing_tables[(x, y)].append(
                RoutingTableEntry(route.outs, key, mask, route.ins)
            )

    return routing_tables


def build_routing_table_target_lengths(system_info):
    """Build a dictionary of target routing table lengths from a
    :py:class:`~rig.machine_control.machine_controller.SystemInfo` object.

    Useful in conjunction with :py:func:`~rig.routing_table.minimise_tables`.

    Returns
    -------
    {(x, y): num, ...}
        A dictionary giving the number of free routing table entries on each
        chip on a SpiNNaker system.

        .. note::
            The actual number of entries reported is the size of the largest
            contiguous free block of routing entries in the routing table.
    """
    return {
        (x, y): ci.largest_free_rtr_mc_block
        for (x, y), ci in iteritems(system_info)
    }


def table_is_subset_of(entries_a, entries_b):
    """Check that every key matched by every entry in one table results in the
    same route when checked against the other table.

    For example, the table::

        >>> from rig.routing_table import Routes
        >>> table = [
        ...     RoutingTableEntry({Routes.north, Routes.north_east}, 0x0, 0xf),
        ...     RoutingTableEntry({Routes.east}, 0x1, 0xf),
        ...     RoutingTableEntry({Routes.south_west}, 0x5, 0xf),
        ...     RoutingTableEntry({Routes.north, Routes.north_east}, 0x8, 0xf),
        ...     RoutingTableEntry({Routes.east}, 0x9, 0xf),
        ...     RoutingTableEntry({Routes.south_west}, 0xe, 0xf),
        ...     RoutingTableEntry({Routes.north, Routes.north_east}, 0xc, 0xf),
        ...     RoutingTableEntry({Routes.south, Routes.south_west}, 0x0, 0xb),
        ... ]

    is a functional subset of a minimised version of itself::

        >>> from rig.routing_table.ordered_covering import minimise
        >>> other_table = minimise(table, target_length=None)
        >>> other_table == table
        False
        >>> table_is_subset_of(table, other_table)
        True

    But not vice-versa::

        >>> table_is_subset_of(other_table, table)
        False

    Default routes are taken into account, such that the table::

        >>> table = [
        ...     RoutingTableEntry({Routes.north}, 0x0, 0xf, {Routes.south}),
        ... ]

    is a subset of the empty table::

        >>> table_is_subset_of(table, list())
        True

    Parameters
    ----------
    entries_a : [:py:class:`~rig.routing_table.RoutingTableEntry`, ...]
    entries_b : [:py:class:`~rig.routing_table.RoutingTableEntry`, ...]
        Ordered of lists of routing table entries to compare.

    Returns
    -------
    bool
        True if every key matched in `entries_a` would result in an equivalent
        route for the packet when matched in `entries_b`.
    """
    # Determine which bits we don't need to explicitly test for
    common_xs = get_common_xs(entries_b)

    # For every entry in the first table
    for entry in expand_entries(entries_a, ignore_xs=common_xs):
        # Look at every entry in the second table
        for other_entry in entries_b:
            # If the first entry matches the second
            if other_entry.mask & entry.key == other_entry.key:
                if other_entry.route == entry.route:
                    # If the route is the same then we move on to the next
                    # entry in the first table.
                    break
                else:
                    # Otherwise we return false as the tables are different
                    return False
        else:
            # If we didn't break out of the loop then the entry from the first
            # table never matched an entry in the second table. If the entry
            # from the first table could not be default routed we return False
            # as the tables cannot be equivalent.
            default_routed = False

            if len(entry.route) == 1 and len(entry.sources) == 1:
                source = next(iter(entry.sources))
                sink = next(iter(entry.route))

                if (source is not None and
                        sink.is_link and
                        source is sink.opposite):
                    default_routed = True

            if not default_routed:
                return False

    return True


def intersect(key_a, mask_a, key_b, mask_b):
    """Return if key-mask pairs intersect (i.e., would both match some of the
    same keys).

    For example, the key-mask pairs ``00XX`` and ``001X`` both match the keys
    ``0010`` and ``0011`` (i.e., they do intersect)::

        >>> intersect(0b0000, 0b1100, 0b0010, 0b1110)
        True

    But the key-mask pairs ``00XX`` and ``11XX`` do not match any of the same
    keys (i.e., they do not intersect)::

        >>> intersect(0b0000, 0b1100, 0b1100, 0b1100)
        False

    Parameters
    ----------
    key_a : int
    mask_a : int
        The first key-mask pair
    key_b : int
    mask_b : int
        The second key-mask pair

    Returns
    -------
    bool
        True if the two key-mask pairs intersect otherwise False.
    """
    return (key_a & mask_b) == (key_b & mask_a)


def expand_entry(entry, ignore_xs=0x0):
    """Turn all Xs which are not marked in `ignore_xs` into ``0``\ s and
    ``1``\ s.

    The following will expand any Xs in bits ``1..3``\ ::

        >>> entry = RoutingTableEntry(set(), 0b0100, 0xfffffff0 | 0b1100)
        >>> list(expand_entry(entry, 0xfffffff1)) == [
        ...     RoutingTableEntry(set(), 0b0100, 0xfffffff0 | 0b1110),  # 010X
        ...     RoutingTableEntry(set(), 0b0110, 0xfffffff0 | 0b1110),  # 011X
        ... ]
        True

    Parameters
    ----------
    entry : :py:class:`~rig.routing_table.RoutingTableEntry` or similar
        The entry to expand.
    ignore_xs : int
        Bit-mask of Xs which should not be expanded.

    Yields
    ------
    :py:class:`~rig.routing_table.RoutingTableEntry`
        Routing table entries which represent the original entry but with all
        Xs not masked off by `ignore_xs` replaced with 1s and 0s.
    """
    # Get all the Xs in the entry that are not ignored
    xs = (~entry.key & ~entry.mask) & ~ignore_xs

    # Find the most significant X
    for bit in (1 << i for i in range(31, -1, -1)):
        if bit & xs:
            # Yield all the entries with this bit set as 0
            entry_0 = RoutingTableEntry(entry.route, entry.key,
                                        entry.mask | bit, entry.sources)
            for new_entry in expand_entry(entry_0, ignore_xs):
                yield new_entry

            # And yield all the entries with this bit set as 1
            entry_1 = RoutingTableEntry(entry.route, entry.key | bit,
                                        entry.mask | bit, entry.sources)
            for new_entry in expand_entry(entry_1, ignore_xs):
                yield new_entry

            # Stop looking for Xs
            break
    else:
        # If there are no Xs then yield the entry we were given.
        yield entry


def expand_entries(entries, ignore_xs=None):
    """Turn all Xs which are not ignored in all entries into ``0`` s and
    ``1`` s.

    For example::

        >>> from rig.routing_table import RoutingTableEntry
        >>> entries = [
        ...     RoutingTableEntry(set(), 0b0100, 0xfffffff0 | 0b1100),  # 01XX
        ...     RoutingTableEntry(set(), 0b0010, 0xfffffff0 | 0b0010),  # XX1X
        ... ]
        >>> list(expand_entries(entries)) == [
        ...     RoutingTableEntry(set(), 0b0100, 0xfffffff0 | 0b1110),  # 010X
        ...     RoutingTableEntry(set(), 0b0110, 0xfffffff0 | 0b1110),  # 011X
        ...     RoutingTableEntry(set(), 0b0010, 0xfffffff0 | 0b1110),  # 001X
        ...     RoutingTableEntry(set(), 0b1010, 0xfffffff0 | 0b1110),  # 101X
        ...     RoutingTableEntry(set(), 0b1110, 0xfffffff0 | 0b1110),  # 111X
        ... ]
        True

    Note that the ``X`` in the LSB was retained because it is common to all
    entries.

    Any duplicated entries will be removed (in this case the first and second
    entries will both match ``0000``, so when the second entry is expanded only
    one entry is retained)::

        >>> from rig.routing_table import Routes
        >>> entries = [
        ...     RoutingTableEntry({Routes.north}, 0b0000, 0b1111),  # 0000 -> N
        ...     RoutingTableEntry({Routes.south}, 0b0000, 0b1011),  # 0X00 -> S
        ... ]
        >>> list(expand_entries(entries)) == [
        ...     RoutingTableEntry({Routes.north}, 0b0000, 0b1111),  # 0000 -> N
        ...     RoutingTableEntry({Routes.south}, 0b0100, 0b1111),  # 0100 -> S
        ... ]
        True

    .. warning::

        It is assumed that the input routing table is orthogonal (i.e., there
        are no two entries which would match the same key). If this is not the
        case, any entries which are covered (i.e. unreachable) in the input
        table will be omitted and a warning produced. As a result, all output
        routing tables are guaranteed to be orthogonal.

    Parameters
    ----------
    entries : [:py:class:`~rig.routing_table.RoutingTableEntry`...] or similar
        The entries to expand.

    Other Parameters
    ----------------
    ignore_xs : int
        Mask of bits in which Xs should not be expanded. If None (the default)
        then Xs which are common to all entries will not be expanded.

    Yields
    ------
    :py:class:`~rig.routing_table.RoutingTableEntry`
        Routing table entries which represent the original entries but with all
        Xs not masked off by `ignore_xs` replaced with 1s and 0s.
    """
    # Find the common Xs for the entries
    if ignore_xs is None:
        ignore_xs = get_common_xs(entries)

    # Keep a track of keys that we've seen
    seen_keys = set({})

    # Expand each entry in turn
    for entry in entries:
        for new_entry in expand_entry(entry, ignore_xs):
            if new_entry.key in seen_keys:
                # We've already used this key, warn that the table is
                # over-complete.
                warnings.warn("Table is not orthogonal: Key {:#010x} matches "
                              "multiple entries.".format(new_entry.key))
            else:
                # Mark the key as seen and yield the new entry
                seen_keys.add(new_entry.key)
                yield new_entry


def get_common_xs(entries):
    """Return a mask of where there are Xs in all routing table entries.

    For example ``01XX`` and ``XX1X`` have common Xs in the LSB only, for this
    input this method would return ``0b0001``::

        >>> from rig.routing_table import RoutingTableEntry
        >>> entries = [
        ...     RoutingTableEntry(set(), 0b0100, 0xfffffff0 | 0b1100),  # 01XX
        ...     RoutingTableEntry(set(), 0b0010, 0xfffffff0 | 0b0010),  # XX1X
        ... ]
        >>> print("{:#06b}".format(get_common_xs(entries)))
        0b0001
    """
    # Determine where there are never 1s in the key and mask
    key = 0x00000000
    mask = 0x00000000

    for entry in entries:
        key |= entry.key
        mask |= entry.mask

    # Where there are never 1s in the key or the mask there are Xs which are
    # common to all entries.
    return (~(key | mask)) & 0xffffffff
