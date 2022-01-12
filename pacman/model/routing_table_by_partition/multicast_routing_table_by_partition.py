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
from pacman.exceptions import PacmanInvalidParameterException
import logging

log = logging.getLogger(__name__)


class MulticastRoutingTableByPartition(object):
    """ A set of multicast routing path objects
    """

    __slots__ = [
        # dict mapping (x,y) -> dict mapping (source_vertex, partition_id))
        # -> routing table entry
        "_router_to_entries_map"
    ]

    def __init__(self):
        self._router_to_entries_map = OrderedDict()

    def add_path_entry(
            self, entry, router_x, router_y, source_vertex, partition_id):
        """ Adds a multicast routing path entry

        :param MulticastRoutingTableByPartitionEntry entry: the entry to add
        :param int router_x: the x coord of the router
        :param int router_y: the y coord of the router
        :param source_vertex: The source that will send via this entry
        :type source_vertex: ApplicationVertex or MachineVertex
        :param str partition_id: The id of the partition being sent
        """

        # update router_to_entries_map
        key = (router_x, router_y)
        if key not in self._router_to_entries_map:
            self._router_to_entries_map[key] = OrderedDict()

        source_key = (source_vertex, partition_id)
        if source_key not in self._router_to_entries_map[key]:
            self._router_to_entries_map[key][source_key] = entry
        else:
            try:
                self._router_to_entries_map[key][source_key] = \
                    entry.merge_entry(
                        self._router_to_entries_map[key][source_key])
            except PacmanInvalidParameterException as e:
                log.error(f"Error merging entries on {key} for {source_key}")
                raise e

    def get_routers(self):
        """ Get the coordinates of all stored routers

        :rtype: iterable(tuple(int, int))
        """
        return iter(self._router_to_entries_map.keys())

    @property
    def n_routers(self):
        """ Get the number of routers stored

        :rtype: int
        """
        return len(self._router_to_entries_map)

    def get_entries_for_router(self, router_x, router_y):
        """ Get the set of multicast path entries assigned to this router

        :param int router_x: the x coord of the router
        :param int router_y: the y coord of the router
        :return: all router_path_entries for the router.
        :rtype: dict((ApplicationVertex or MachineVertex), str),\
            MulticastRoutingTableByPartitionEntry)
        """
        key = (router_x, router_y)
        return self._router_to_entries_map.get(key)

    def get_entry_on_coords_for_edge(
            self, source_vertex, partition_id, router_x, router_y):
        """ Get an entry from a specific coordinate

        :param source_vertex:
        :type source_vertex: ApplicationVertex or MachineVertex
        :param str partition_id:
        :param int router_x: the x coord of the router
        :param int router_y: the y coord of the router
        :rtype: MulticastRoutingTableByPartitionEntry or None
        """
        entries = self.get_entries_for_router(router_x, router_y)
        if entries is None:
            return None
        return entries.get((source_vertex, partition_id))
