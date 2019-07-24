# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
based on
https://github.com/project-rig/rig/blob/master/rig/routing_table/remove_default_routes.py
"""

from pacman.exceptions import MinimisationFailedError
from .utils import intersect


def minimise(table, target_length, check_for_aliases=True):
    """
    Remove from the routing table any entries which could be replaced by
    default routing.

    :param routing_table: Routing entries to be merged.
    :type routing_table: RoutingTableEntry
    :param target_length :
        Target length of the routing table; the minimisation procedure will
        halt once either this target is reached or no further minimisation is
        possible. If None then the table will be made as small as possible.
    :type target_length : int or None
    :param check_for_aliases:
        If True (the default), default-route candidates are checked for aliased
        entries before suggesting a route may be default routed. This check is
        required to ensure correctness in the general case but has a runtime
        complexity of O(N^2) in the worst case for N-entry tables.

        If False, the alias-check is skipped resulting in O(N) runtime. This
        option should only be used if the supplied table is guaranteed not to
        contain any aliased entries.

    :return: list(RoutingTableEntry)
    :raises MinimisationFailedError
        If the smallest table that can be produced is larger than
        `target_length`.
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
        elif check_for_aliases:
            key, mask = entry.key, entry.mask
            # If there is an intersect with a later entry we have to keep it
            if any(intersect(key, mask, d.key, d.mask) for
                    d in table[i + 1:]):
                new_table.append(entry)

        # If the resultant table is larger than the target raise an exception
    if target_length is not None and target_length < len(new_table):
        raise MinimisationFailedError(target_length, len(new_table))

    return new_table
