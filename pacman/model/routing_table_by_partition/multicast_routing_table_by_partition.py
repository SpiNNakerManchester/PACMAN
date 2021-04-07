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

from collections import OrderedDict


class MulticastRoutingTableByPartition(object):
    """ A set of multicast routing path objects
    """

    __slots__ = [
        # dict mapping (x,y) -> dict mapping (partition) -> routing table entry
        "_router_to_entries_map"
    ]

    def __init__(self):
        self._router_to_entries_map = OrderedDict()

    def add_path_entry(self, entry, router_x, router_y, partition):
        """ Adds a multicast routing path entry

        :param MulticastRoutingTableByPartitionEntry entry: the entry to add
        :param int router_x: the x coord of the router
        :param int router_y: the y coord of the router
        :param AbstractSingleSourcePartition partition:\
            the partition containing the machine edge
        """

        # update router_to_entries_map
        key = (router_x, router_y)
        if key not in self._router_to_entries_map:
            self._router_to_entries_map[key] = OrderedDict()

        if partition not in self._router_to_entries_map[key]:
            self._router_to_entries_map[key][partition] = entry
        else:
            self._router_to_entries_map[key][partition] = entry.merge_entry(
                self._router_to_entries_map[key][partition])

    def get_routers(self):
        """ Get the coordinates of all stored routers

        :rtype: iterable(tuple(int, int))
        """
        return iter(self._router_to_entries_map.keys())

    def get_entries_for_router(self, router_x, router_y):
        """ Get the set of multicast path entries assigned to this router

        :param int router_x: the x coord of the router
        :param int router_y: the y coord of the router
        :return: all router_path_entries for the router.
        :rtype: dict(AbstractSingleSourcePartition,\
            MulticastRoutingTableByPartitionEntry)
        """
        key = (router_x, router_y)
        if key not in self._router_to_entries_map:
            return ()
        return self._router_to_entries_map[key]

    def get_entry_on_coords_for_edge(self, partition, router_x, router_y):
        """ Get an entry from a specific coordinate

        :param AbstractSingleSourcePartition partition:
        :param int router_x: the x coord of the router
        :param int router_y: the y coord of the router
        :rtype: MulticastRoutingTableByPartitionEntry or None
        """
        entries = self.get_entries_for_router(router_x, router_y)
        if partition in entries:
            return entries[partition]
        return None
