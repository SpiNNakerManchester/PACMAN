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
based on https://github.com/project-rig/
"""

from abc import abstractmethod
import logging
from spinn_utilities.config_holder import get_config_bool
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import Machine
from pacman.data import PacmanDataView
from pacman.model.routing_tables import (
    CompressedMulticastRoutingTable, MulticastRoutingTables)
from pacman.exceptions import MinimisationFailedError

logger = FormatAdapter(logging.getLogger(__name__))


class AbstractCompressor(object):

    __slots__ = [
        # String of problems detected. Must be "" to finish
        "_problems",
        # Flag to say if the results can be order dependent
        "_ordered",
        # Flag to say that results too large should be ignored
        "_accept_overflow"
    ]

    def __init__(self, ordered=True, accept_overflow=False):
        self._ordered = ordered
        self._accept_overflow = accept_overflow
        self._problems = ""

    def _run(self):
        """
        :rtype: MulticastRoutingTables
        """
        router_tables = PacmanDataView.get_precompressed()
        # create progress bar
        progress = ProgressBar(
            router_tables.routing_tables,
            "Compressing routing Tables using {}".format(
                self.__class__.__name__))
        return self.compress_tables(router_tables, progress)

    @abstractmethod
    def compress_table(self, router_table):
        """
        :param UnCompressedMulticastRoutingTable router_table:
            Original routing table for a single chip
        :return: Raw compressed routing table entries for the same chip
        :rtype: list(Entry)
        """

    def compress_tables(self, router_tables, progress):
        """ Compress all the unordered routing tables

        Tables who start of smaller than target_length are not compressed

        :param MulticastRoutingTables router_tables: Routing tables
        :param ~spinn_utilities.progress_bar.ProgressBar progress:
            Progress bar to show while working
        :return: The compressed but still unordered routing tables
        :rtype: MulticastRoutingTables
        :raises MinimisationFailedError: on failure
        """
        compressed_tables = MulticastRoutingTables()
        if get_config_bool(
                "Mapping", "router_table_compress_as_far_as_possible"):
            # Compress as much as possible
            target_length = 0
        else:
            target_length = Machine.ROUTER_ENTRIES
        for table in progress.over(router_tables.routing_tables):
            if table.number_of_entries < target_length:
                new_table = table
            else:
                compressed_table = self.compress_table(table)

                new_table = CompressedMulticastRoutingTable(table.x, table.y)

                for entry in compressed_table:
                    new_table.add_multicast_routing_entry(
                        entry.to_MulticastRoutingEntry())
                if new_table.number_of_entries > Machine.ROUTER_ENTRIES:
                    self._problems += "(x:{},y:{})={} ".format(
                        new_table.x, new_table.y, new_table.number_of_entries)

            compressed_tables.add_routing_table(new_table)

        if len(self._problems) > 0:
            if self._ordered and not self._accept_overflow:
                raise MinimisationFailedError(
                    "The routing table after compression will still not fit"
                    " within the machines router: {}".format(self._problems))
            else:
                logger.warning(self._problems)
        return compressed_tables
