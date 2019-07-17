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

import collections
import logging
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import MulticastRoutingEntry
from pacman.model.routing_tables import (
    MulticastRoutingTable, MulticastRoutingTables)
from pacman.exceptions import PacmanElementAllocationException
from .routing_table_entry import RoutingTableEntry
from pacman.operations.router_compressors.mundys_router_compressor import \
    ordered_covering as rigs_compressor

logger = logging.getLogger(__name__)


class MundyRouterCompressor(object):
    """ Compressor from rig that has been tied into the main tool chain stack.
    """

    __slots__ = []

    max_supported_length = 1023

    def __call__(self, router_tables, target_length=None):
        # build storage
        compressed_pacman_router_tables = MulticastRoutingTables()

        # create progress bar
        progress = ProgressBar(
            router_tables.routing_tables, "Compressing routing Tables")

        # compress each router
        for router_table in progress.over(router_tables.routing_tables):
            # convert to rig format
            entries = self._convert_to_mundy_format(router_table)

            # compress the router entries
            compressed_router_table_entries = \
                rigs_compressor.minimise(entries, target_length)

            # convert back to pacman model
            compressed_pacman_table = self._convert_to_pacman_router_table(
                compressed_router_table_entries, router_table.x,
                router_table.y)

            # add to new compressed routing tables
            compressed_pacman_router_tables.add_routing_table(
                compressed_pacman_table)

        # return
        return compressed_pacman_router_tables

    @staticmethod
    def _convert_to_mundy_format(pacman_router_table):
        """
        :param pacman_router_table: pacman version of the routing table
        :return: rig version of the router table
        """
        entries = list()

        # handle entries
        for router_entry in pacman_router_table.multicast_routing_entries:
            # Get the route for the entry
            new_processor_ids = list()
            for processor_id in router_entry.processor_ids:
                new_processor_ids.append(processor_id + 6)

            route = router_entry.spinnaker_route

            # Add the new entry
            entries.append(RoutingTableEntry(
                route, router_entry.routing_entry_key, router_entry.mask,
                router_entry.defaultable))

        return entries

    def _convert_to_pacman_router_table(
            self, mundy_compressed_router_table_entries, router_x_coord,
            router_y_coord):
        """
        :param mundy_compressed_router_table_entries: rig version of the table
        :param router_x_coord: the x coord of this routing table
        :param router_y_coord: the y coord of this routing table
        :return: pacman version of the table
        """

        table = MulticastRoutingTable(router_x_coord, router_y_coord)
        if (len(mundy_compressed_router_table_entries) >
                self.max_supported_length):
            raise PacmanElementAllocationException(
                "The routing table {}:{} after compression will still not fit"
                " within the machines router ({} entries)".format(
                    router_x_coord, router_y_coord,
                    len(mundy_compressed_router_table_entries)))

        for entry in mundy_compressed_router_table_entries:
            table.add_multicast_routing_entry(MulticastRoutingEntry(
                entry.key, entry.mask,  defaultable=False,  # NOT defaultable
                spinnaker_route=entry.route,
                ))
        return table
