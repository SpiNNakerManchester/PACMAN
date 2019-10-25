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
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.routing_tables import (
    MulticastRoutingTable, MulticastRoutingTables)
from pacman.exceptions import MinimisationFailedError

logger = logging.getLogger(__name__)


class AbstractCompressor(object):

    MAX_SUPPORTED_LENGTH = 1023

    __slots__ = [
        # Max length below which the algorithm should stop compressing
        "_target_length",
        # String of problems detected. Must be "" to finish
        "_problems",
        # Flag to say if the results can be order dependent
        "_ordered",
    ]

    def __init__(self, ordered=True):
        self._ordered = ordered

    def __call__(self, router_tables, target_length=None):
        if target_length is None:
            self._target_length = 0  # Compress as much as you can
        else:
            self._target_length = target_length
        # create progress bar
        progress = ProgressBar(
            router_tables.routing_tables,
            "Compressing routing Tables using {}".format(
                self.__class__.__name__))
        return self.compress_tables(router_tables, progress)

    @staticmethod
    def intersect(key_a, mask_a, key_b, mask_b):
        """
        Return if key-mask pairs intersect (i.e., would both match some of
        the same keys).

        For example, the key-mask pairs ``00XX`` and ``001X`` both match the
        keys``0010`` and ``0011`` (i.e., they do intersect)::

            >>> intersect(0b0000, 0b1100, 0b0010, 0b1110)
            True

        But the key-mask pairs ``00XX`` and ``11XX`` do not match any of the
        same keys (i.e., they do not intersect)::

            >>> intersect(0b0000, 0b1100, 0b1100, 0b1100)
            False

        :param key_a: The key of first key-mask pair
        :type key_a: int
        :param mask_a: The mask of first key-mask pair
        :type key_b: int
        :param key_b: The key of second key-mask pair
        :type key_b: int
        :param mask_b: The mask of second key-mask pair
        :type key_b: int
        :return: True if the two key-mask pairs intersect otherwise False.
        :rtype: bool
        """
        return (key_a & mask_b) == (key_b & mask_a)

    def merge(self, entry1, entry2):
        """
        Merges two entries/triples into one that covers both

        The assumption is that they both have the same known spinnaker_route

        :param entry1: Key, Mask, defaultable from the first entry
        :type entry1: Entry
        :param entry2: Key, Mask, defaultable from the second entry
        :type entry2: Entry
        :return: Key, Mask, defaultable from merged entry
        :rtype: (int, int, bool)
        """
        any_ones = entry1.key | entry2.key
        all_ones = entry1.key & entry2.key
        all_selected = entry1.mask & entry2.mask

        # Compute the new mask  and key
        any_zeros = ~all_ones
        new_xs = any_ones ^ any_zeros
        mask = all_selected & new_xs  # Combine existing and new Xs
        key = all_ones & mask
        return key, mask, entry1.defaultable and entry2.defaultable

    @abstractmethod
    def compress_table(self, router_table):
        pass

    def compress_tables(self, router_tables, progress):
        """
        Compress all the unordered routing tables

        Tables who start of smaller than target_length are not compressed

        :param router_tables: Routing tables
        :type router_tables: MulticastRoutingTables
        :param progress: Progress bar to show while working
        :tpye progress: ProgressBar
        :return: The compressed but still unordered routing tables
        """
        compressed_tables = MulticastRoutingTables()
        self._problems = ""
        for table in progress.over(router_tables.routing_tables):
            if table.number_of_entries < self._target_length:
                new_table = table
            else:
                compressed_table = self.compress_table(table)

                new_table = MulticastRoutingTable(table.x, table.y)

                for entry in compressed_table:
                    new_table.add_multicast_routing_entry(
                        entry.to_MulticastRoutingEntry())
                if new_table.number_of_entries > self.MAX_SUPPORTED_LENGTH:
                    self._problems += "(x:{},y:{})={} ".format(
                        new_table.x, new_table.y, new_table.number_of_entries)

            compressed_tables.add_routing_table(new_table)

        if len(self._problems) > 0:
            if self._ordered:
                raise MinimisationFailedError(
                    "The routing table after compression will still not fit"
                    " within the machines router: {}".format(self._problems))
            else:
                logger.warning(self._problems)
        return compressed_tables

    @property
    def ordered(self):
        return self._ordered
