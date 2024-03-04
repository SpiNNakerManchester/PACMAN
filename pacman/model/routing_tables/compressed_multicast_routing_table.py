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
from typing import Any, Collection, Iterable, List
from spinn_utilities.overrides import overrides
from spinn_machine.multicast_routing_entry import MulticastRoutingEntry
from pacman.model.routing_tables import AbstractMulticastRoutingTable


class CompressedMulticastRoutingTable(AbstractMulticastRoutingTable):
    """
    Represents a compressed routing table for a chip.
    Compressed tables have a maximum size, ensuring that they fit in the
    hardware available.
    """

    __slots__ = (
        # The coordinates of the chip for which this is the routing table
        "_x", "_y",

        # An iterable of routing entries to add to the table
        "_multicast_routing_entries",

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
        :raise pacman.exceptions.PacmanAlreadyExistsException:
            If any two routing entries contain the same key-mask combination
        """
        self._x = x
        self._y = y
        self._number_of_defaulted_routing_entries = 0
        self._multicast_routing_entries: List[MulticastRoutingEntry] = list()

        for multicast_routing_entry in multicast_routing_entries:
            self.add_multicast_routing_entry(multicast_routing_entry)

    @overrides(AbstractMulticastRoutingTable.add_multicast_routing_entry)
    def add_multicast_routing_entry(
            self, multicast_routing_entry: MulticastRoutingEntry):
        self._multicast_routing_entries.append(multicast_routing_entry)

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
        return self._multicast_routing_entries

    @property
    @overrides(AbstractMulticastRoutingTable.number_of_entries)
    def number_of_entries(self) -> int:
        return len(self._multicast_routing_entries)

    @property
    @overrides(AbstractMulticastRoutingTable.number_of_defaultable_entries)
    def number_of_defaultable_entries(self) -> int:
        return self._number_of_defaulted_routing_entries

    @overrides(AbstractMulticastRoutingTable.__eq__)
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CompressedMulticastRoutingTable):
            return False
        if self._x != other.x and self._y != other.y:
            return False
        return self._multicast_routing_entries == \
            other.multicast_routing_entries

    @overrides(AbstractMulticastRoutingTable.__hash__)
    def __hash__(self) -> int:
        return id(self)
