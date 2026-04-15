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
https://github.com/project-rig/rig/blob/master/rig/routing_table/utils.py
and
https://github.com/project-rig/rig/blob/master/rig/routing_table/remove_default_routes.py
"""

from typing import List, Optional
from spinn_machine import MulticastRoutingEntry
from pacman.exceptions import MinimisationFailedError


def intersect(key_a: int, mask_a: int, key_b: int, mask_b: int) -> bool:
    """
    Return if key-mask pairs intersect (i.e., would both match some of the
    same keys).

    For example, the key-mask pairs ``00XX`` and ``001X`` both match the keys
    ``0010`` and ``0011`` (i.e., they do intersect)::

        >>> intersect(0b0000, 0b1100, 0b0010, 0b1110)
        True

    But the key-mask pairs ``00XX`` and ``11XX`` do not match any of the same
    keys (i.e., they do not intersect)::

        >>> intersect(0b0000, 0b1100, 0b1100, 0b1100)
        False

    :param key_a:
    :param mask_a: The first key-mask pair
    :param key_b:
    :param mask_b: The second key-mask pair
    :return: True if the two key-mask pairs intersect, otherwise False.
    """
    return (key_a & mask_b) == (key_b & mask_a)


def remove_default_routes(
        table: List[MulticastRoutingEntry], target_length: Optional[int],
        check_for_aliases: bool = True) -> List[MulticastRoutingEntry]:
    """
    Remove from the routing table any entries which could be replaced by
    default routing.

    :param table: Routing entries to be merged.
    :param target_length:
        Target length of the routing table; the minimisation procedure will
        halt once either this target is reached or no further minimisation is
        possible. If ``None`` then the table will be made as small as possible.
    :param check_for_aliases:
        If ``True`` (the default), default-route candidates are checked for
        aliased entries before suggesting a route may be default routed. This
        check is required to ensure correctness in the general case but has a
        runtime complexity of O(N\\ :sup:`2`) in the worst case for N-entry
        tables.

        If ``False``, the alias-check is skipped resulting in O(N) runtime.
        This option should only be used if the supplied table is guaranteed not
        to contain any aliased entries.
    :returns: The none default entries.
    :raises MinimisationFailedError:
        If the smallest table that can be produced is larger than
        ``target_length``.
    """
    # If alias checking is required, see if we can cheaply prove that no
    # aliases exist in the table to skip this costly check.
    if check_for_aliases:
        # Aliases cannot exist when all entries share the same mask and all
        # keys are unique.
        if len(frozenset(e.mask for e in table)) == 1 and \
                len(table) == len(frozenset(e.key for e in table)):
            check_for_aliases = False

    # Generate a new table with default-route entries removed
    if not check_for_aliases:
        # Optimised case: no alias check so just remove default-routed entries
        new_table = [entry for entry in table if not entry.defaultable]
    else:
        new_table = list()
        for i, entry in enumerate(table):
            if not entry.defaultable:
                # If the entry cannot be removed then add it to the table
                new_table.append(entry)
            else:
                # If there is an intersect with a later entry we must keep it
                if any(intersect(entry.key, entry.mask, d.key, d.mask) for
                       d in table[i + 1:]):
                    new_table.append(entry)

    if target_length and len(new_table) > target_length:
        raise MinimisationFailedError(
            f"Best compression is {len(new_table)} which is "
            f"still higher than the target {target_length}")

    return new_table
