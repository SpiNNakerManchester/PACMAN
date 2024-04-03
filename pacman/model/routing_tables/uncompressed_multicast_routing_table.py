# Copyright (c) 2014 The University of Manchester
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

import csv
import gzip
import logging
from typing import Any, Collection, Dict, Iterable

from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spinn_machine import MulticastRoutingEntry
from pacman.exceptions import PacmanAlreadyExistsException
from pacman.model.routing_tables import AbstractMulticastRoutingTable

logger = FormatAdapter(logging.getLogger(__name__))


class UnCompressedMulticastRoutingTable(AbstractMulticastRoutingTable):
    """
    Represents a uncompressed routing table for a chip.
    Uncompressed tables have no maximum size, but may not be deployable to
    hardware without being compressed.
    """

    __slots__ = (
        # The coordinates of the chip for which this is the routing table
        "_x", "_y",

        # dict of multicast routing entries.
        # (key, mask) -> multicast_routing_entry
        "_entries_by_key_mask",

        # counter of how many entries in their multicast routing table are
        # defaultable
        "_number_of_defaulted_routing_entries")

    def __init__(
            self, x: int, y: int,
            multicast_routing_entries: Iterable[MulticastRoutingEntry] = ()):
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
        self._entries_by_key_mask: Dict = dict()

        for multicast_routing_entry in multicast_routing_entries:
            self.add_multicast_routing_entry(multicast_routing_entry)

    @overrides(AbstractMulticastRoutingTable.add_multicast_routing_entry)
    def add_multicast_routing_entry(
            self, multicast_routing_entry: MulticastRoutingEntry):
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
    def x(self) -> int:
        return self._x

    @property
    @overrides(AbstractMulticastRoutingTable.y)
    def y(self) -> int:
        return self._y

    @property
    @overrides(AbstractMulticastRoutingTable.multicast_routing_entries)
    def multicast_routing_entries(self) -> Collection[MulticastRoutingEntry]:
        return self._entries_by_key_mask.values()

    @property
    @overrides(AbstractMulticastRoutingTable.number_of_entries)
    def number_of_entries(self) -> int:
        return len(self._entries_by_key_mask)

    @property
    @overrides(AbstractMulticastRoutingTable.number_of_defaultable_entries)
    def number_of_defaultable_entries(self) -> int:
        return self._number_of_defaulted_routing_entries

    @overrides(AbstractMulticastRoutingTable.__eq__)
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, UnCompressedMulticastRoutingTable):
            return False
        if self._x != other.x and self._y != other.y:
            return False
        return self._entries_by_key_mask == other._entries_by_key_mask

    @overrides(AbstractMulticastRoutingTable.__hash__)
    def __hash__(self) -> int:
        return id(self)


def _from_csv_file(
        csvfile: Iterable[str]) -> UnCompressedMulticastRoutingTable:
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


def from_csv(file_name: str) -> UnCompressedMulticastRoutingTable:
    """
    Reads a comma separated file into Routing Tables

    :param str file_name:
    :rtype: UnCompressedMulticastRoutingTable:
    """
    if file_name.endswith(".gz"):
        with gzip.open(file_name, mode="rt", newline='') as csvfile:
            return _from_csv_file(csvfile)
    else:
        with open(file_name, newline='', encoding="utf-8") as csvfile:
            return _from_csv_file(csvfile)
