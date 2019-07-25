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

import logging
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import MulticastRoutingEntry
from pacman.model.routing_tables import (
    MulticastRoutingTable, MulticastRoutingTables)
from pacman.operations.router_compressors import (AbstractCompressor, Entry)
from pacman.exceptions import PacmanElementAllocationException
from pacman.operations.router_compressors.mundys_router_compressor import \
    ordered_covering as rigs_compressor

logger = logging.getLogger(__name__)


class MundyRouterCompressor(AbstractCompressor):
    """ Compressor from rig that has been tied into the main tool chain stack.
    """

    __slots__ = []

    def compress_table(self, router_table):
        # convert to rig inspired format
        entries = self._convert_to_mundy_format(router_table)

        compressed_router_table_entries = \
            rigs_compressor.minimise(entries, self._target_length)

        # compress the router entries
        return  compressed_router_table_entries

    @staticmethod
    def _convert_to_mundy_format(pacman_router_table):
        """
        :param pacman_router_table: pacman version of the routing table
        :return: rig version of the router table
        """
        entries = list()

        # handle entries
        for router_entry in pacman_router_table.multicast_routing_entries:
            # Add the new entry
            entries.append(Entry.from_MulticastRoutingEntry(router_entry))

        return entries
