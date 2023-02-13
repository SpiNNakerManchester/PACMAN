# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import gzip
import logging
from spinn_utilities.log import FormatAdapter
from spinn_machine import MulticastRoutingEntry
from pacman.exceptions import PacmanAlreadyExistsException
from pacman.model.routing_tables import AbstractMulticastRoutingTable
from spinn_utilities.overrides import overrides

logger = FormatAdapter(logging.getLogger(__name__))


class UnCompressedMulticastRoutingTable(AbstractMulticastRoutingTable):
    """ Represents a uncompressed routing table for a chip.
    """

    __slots__ = [
        # The x-coordinate of the chip for which this is the routing table
        "_x",

        # The y-coordinate of the chip for which this is the routing tables
        "_y",

        # dict of multicast routing entries.
        # (key, mask) -> multicast_routing_entry
        "_entries_by_key_mask",

        # counter of how many entries in their multicast routing table are
        # defaultable
        "_number_of_defaulted_routing_entries"
    ]

    def __init__(self, x, y, multicast_routing_entries=None):
        """
        :param int x:
            The x-coordinate of the chip for which this is the routing table
        :param int y:
            The y-coordinate of the chip for which this is the routing tables
        :param multicast_routing_entries:
            The routing entries to add to the table
        :type multicast_routing_entries:
            iterable(~spinn_machine.MulticastRoutingEntry)
        :raise PacmanAlreadyExistsException:
            If any two routing entries contain the same key-mask combination
        """
        self._x = x
        self._y = y
        self._number_of_defaulted_routing_entries = 0
        self._entries_by_key_mask = dict()

        if multicast_routing_entries is not None:
            for multicast_routing_entry in multicast_routing_entries:
                self.add_multicast_routing_entry(multicast_routing_entry)

    def add_multicast_routing_entry(self, multicast_routing_entry):
        """ Adds a routing entry to this table

        :param ~spinn_machine.MulticastRoutingEntry multicast_routing_entry:
            The route to add
        :rtype: None
        :raise PacmanAlreadyExistsException:
            If a routing entry with the same key-mask combination already
            exists
        """
        routing_entry_key = multicast_routing_entry.routing_entry_key
        mask = multicast_routing_entry.mask

        tuple_key = (routing_entry_key, mask)
        if tuple_key in self._entries_by_key_mask:
            # Only fail if they don't go to the same place
            if self._entries_by_key_mask[tuple_key] == multicast_routing_entry:
                return
            raise PacmanAlreadyExistsException(
                f"Multicast_routing_entry {tuple_key}: "
                f"{self._entries_by_key_mask[tuple_key]} on "
                f"{self._x}, {self._y}",
                str(multicast_routing_entry))

        self._entries_by_key_mask[tuple_key] = multicast_routing_entry

        # update default routed counter if required
        if multicast_routing_entry.defaultable:
            self._number_of_defaulted_routing_entries += 1

    @property
    @overrides(AbstractMulticastRoutingTable.x)
    def x(self):
        """ The x-coordinate of the chip of this table

        :rtype: int
        """
        return self._x

    @property
    @overrides(AbstractMulticastRoutingTable.y)
    def y(self):
        """ The y-coordinate of the chip of this table

        :rtype: int
        """
        return self._y

    @property
    @overrides(AbstractMulticastRoutingTable.multicast_routing_entries)
    def multicast_routing_entries(self):
        """ The multicast routing entries in the table

        :rtype: iterable(~spinn_machine.MulticastRoutingEntry)
        :raise None: does not raise any known exceptions
        """
        return self._entries_by_key_mask.values()

    @property
    @overrides(AbstractMulticastRoutingTable.number_of_entries)
    def number_of_entries(self):
        """ The number of multicast routing entries there are in the\
            multicast routing table

        :rtype: int
        """
        return len(self._entries_by_key_mask)

    @property
    @overrides(AbstractMulticastRoutingTable.number_of_defaultable_entries)
    def number_of_defaultable_entries(self):
        """ The number of multicast routing entries that are set to be\
            defaultable within this multicast routing table

        :rtype: int
        """
        return self._number_of_defaulted_routing_entries

    @overrides(AbstractMulticastRoutingTable.__eq__)
    def __eq__(self, other):
        if not isinstance(other, UnCompressedMulticastRoutingTable):
            return False
        if self._x != other.x and self._y != other.y:
            return False
        return self._entries_by_key_mask == other._entries_by_key_mask

    @overrides(AbstractMulticastRoutingTable.__ne__)
    def __ne__(self, other):
        return not self.__eq__(other)

    @overrides(AbstractMulticastRoutingTable.__repr__)
    def __repr__(self):
        entry_string = ""
        for entry in self.multicast_routing_entries:
            entry_string += "{}\n".format(entry)
        return "{}:{}\n\n{}".format(self._x, self._y, entry_string)

    @overrides(AbstractMulticastRoutingTable.__hash__)
    def __hash__(self):
        return id(self)


def _from_csv_file(csvfile):
    table_reader = csv.reader(csvfile)
    table = UnCompressedMulticastRoutingTable(0, 0)
    for row in table_reader:
        try:
            if len(row) == 3:
                key = int(row[0], base=16)
                mask = int(row[1], base=16)
                route = int(row[2], base=16)
                table.add_multicast_routing_entry(
                    MulticastRoutingEntry(key, mask, spinnaker_route=route))
            elif len(row) == 6:
                key = int(row[1], base=16)
                mask = int(row[2], base=16)
                route = int(row[3], base=16)
                table.add_multicast_routing_entry(
                    MulticastRoutingEntry(key, mask, spinnaker_route=route))
        except ValueError as ex:
            logger.warning(f"csv read error {ex}")
    return table


def from_csv(file_name):
    if file_name.endswith(".gz"):
        with gzip.open(file_name, mode="rt", newline='') as csvfile:
            return _from_csv_file(csvfile)
    else:
        with open(file_name, newline='', encoding="utf-8") as csvfile:
            return _from_csv_file(csvfile)
