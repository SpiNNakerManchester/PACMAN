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
