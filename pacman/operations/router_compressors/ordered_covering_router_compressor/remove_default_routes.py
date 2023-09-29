# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
based on
https://github.com/project-rig/rig/blob/master/rig/routing_table/remove_default_routes.py
"""

from .utils import intersect
from pacman.exceptions import MinimisationFailedError


def remove_default_routes(table, target_length, check_for_aliases=True):
    """
    Remove from the routing table any entries which could be replaced by
    default routing.

    :param list(Entry) table: Routing entries to be merged.
    :param target_length:
        Target length of the routing table; the minimisation procedure will
        halt once either this target is reached or no further minimisation is
        possible. If ``None`` then the table will be made as small as possible.
    :type target_length: int or None
    :param bool check_for_aliases:
        If ``True`` (the default), default-route candidates are checked for
        aliased entries before suggesting a route may be default routed. This
        check is required to ensure correctness in the general case but has a
        runtime complexity of O(N\\ :sup:`2`) in the worst case for N-entry
        tables.

        If ``False``, the alias-check is skipped resulting in O(N) runtime.
        This option should only be used if the supplied table is guaranteed not
        to contain any aliased entries.
    :rtype: list(Entry)
    :raises MinimisationFailedError:
        If the smallest table that can be produced is larger than
        ``target_length``.
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

    if target_length and len(new_table) > target_length:
        raise MinimisationFailedError(
            f"Best compression is {len(new_table)} which is "
            f"still higher than the target {target_length}")

    return new_table
