"""
based on
https://github.com/project-rig/rig/blob/master/rig/routing_table/remove_default_routes.py
"""

from pacman.operations.router_compressors.mundys_router_compressor.exceptions \
    import MinimisationFailedError


def minimise(table, target_length, check_for_aliases=True):
    """Remove from the routing table any entries which could be replaced by
    default routing.

    Parameters
    ----------
    routing_table : [:py:class:`~rig.routing_table.RoutingTableEntry`, ...]
        Routing table from which to remove entries which could be handled by
        default routing.
    target_length : int or None
        Target length of the routing table.
    check_for_aliases : bool
        If True (the default), default-route candidates are checked for aliased
        entries before suggesting a route may be default routed. This check is
        required to ensure correctness in the general case but has a runtime
        complexity of O(N^2) in the worst case for N-entry tables.

        If False, the alias-check is skipped resulting in O(N) runtime. This
        option should only be used if the supplied table is guaranteed not to
        contain any aliased entries.

    Raises
    ------
    MinimisationFailedError
        If the smallest table that can be produced is larger than
        `target_length`.

    Returns
    -------
    [:py:class:`~rig.routing_table.RoutingTableEntry`, ...]
        Reduced routing table entries.
    """
    # If alias checking is required, see if we can cheaply prove that no
    # aliases exist in the table to skip this costly check.
    if check_for_aliases:
        # Aliases cannot exist when all entries share the same mask and all
        # keys are unique.
        if len(set(e.mask for e in table)) == 1 and \
                len(table) == len(set(e.key for e in table)):
            check_for_aliases = False

    # Generate a new table with default-route entries removed
    new_table = list()
    for i, entry in enumerate(table):
        if not entry.defaultable:
            # If the entry cannot be removed then add it to the table
            new_table.append(entry)

    # If the resultant table is larger than the target raise an exception
    if target_length is not None and target_length < len(new_table):
        raise MinimisationFailedError(target_length, len(new_table))

    return new_table


def _is_defaultable(i, entry, table, check_for_aliases=True):
    """Determine if an entry may be removed from a routing table and be
    replaced by a default route.

    Parameters
    ----------
    i : int
        Position of the entry in the table
    entry : RoutingTableEntry
        The entry itself
    table : [RoutingTableEntry, ...]
        The table containing the entry.
    check_for_aliases : bool
        If True, the table is checked for aliased entries before suggesting a
        route may be default routed.
    """
    # May only have one source and sink (which may not be None)
