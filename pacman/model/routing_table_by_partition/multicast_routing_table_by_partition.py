# Copyright (c) 2015 The University of Manchester
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

from pacman.model.graphs.application import ApplicationVertex
from pacman.exceptions import PacmanInvalidParameterException
import logging

log = logging.getLogger(__name__)


class MulticastRoutingTableByPartition(object):
    """
    A set of multicast routing path objects.
    """

    __slots__ = [
        # dict mapping (x,y) -> dict mapping (source_vertex, partition_id))
        # -> routing table entry
        "_router_to_entries_map"
    ]

    def __init__(self):
        self._router_to_entries_map = dict()

    def add_path_entry(
            self, entry, router_x, router_y, source_vertex, partition_id):
        """
        Adds a multicast routing path entry.

        :param MulticastRoutingTableByPartitionEntry entry: the entry to add
        :param int router_x: the X coordinate of the router
        :param int router_y: the Y coordinate of the router
        :param source_vertex: The source that will send via this entry
        :type source_vertex: ApplicationVertex or MachineVertex
        :param str partition_id: The ID of the partition being sent
        """

        # update router_to_entries_map
        key = (router_x, router_y)
        entries = self._router_to_entries_map.get(key)
        if entries is None:
            entries = dict()
            self._router_to_entries_map[key] = entries

        if isinstance(source_vertex, ApplicationVertex):
            for m_vert in source_vertex.machine_vertices:
                if (m_vert, partition_id) in entries:
                    raise PacmanInvalidParameterException(
                        "source_vertex", source_vertex,
                        f"Route for Machine vertex {m_vert}, "
                        f"partition {partition_id} already in table")
        else:
            if (source_vertex.app_vertex, partition_id) in entries:
                raise PacmanInvalidParameterException(
                    "source_vertex", source_vertex,
                    f"Route for Application vertex {source_vertex.app_vertex}"
                    f" partition {partition_id} already in table")

        source_key = (source_vertex, partition_id)
        if source_key not in entries:
            entries[source_key] = entry
        else:
            try:
                entries[source_key] = entry.merge_entry(entries[source_key])
            except PacmanInvalidParameterException as e:
                log.error(
                    "Error merging entries on %s for %s", key, source_key)
                raise e

    def get_routers(self):
        """
        Get the coordinates of all stored routers.

        :rtype: iterable(tuple(int, int))
        """
        return iter(self._router_to_entries_map.keys())

    @property
    def n_routers(self):
        """
        The number of routers stored.

        :rtype: int
        """
        return len(self._router_to_entries_map)

    def get_entries_for_router(self, router_x, router_y):
        """
        Get the set of multicast path entries assigned to this router.

        :param int router_x: the X coordinate of the router
        :param int router_y: the Y coordinate of the router
        :return: all router_path_entries for the router.
        :rtype: dict((ApplicationVertex or MachineVertex), str),
            MulticastRoutingTableByPartitionEntry)
        """
        key = (router_x, router_y)
        return self._router_to_entries_map.get(key)

    def get_entry_on_coords_for_edge(
            self, source_vertex, partition_id, router_x, router_y):
        """
        Get an entry from a specific coordinate.

        :param source_vertex:
        :type source_vertex: ApplicationVertex or MachineVertex
        :param str partition_id:
        :param int router_x: the X coordinate of the router
        :param int router_y: the Y coordinate of the router
        :rtype: MulticastRoutingTableByPartitionEntry or None
        """
        entries = self.get_entries_for_router(router_x, router_y)
        if entries is None:
            return None
        return entries.get((source_vertex, partition_id))
