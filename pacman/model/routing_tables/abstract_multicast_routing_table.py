# Copyright (c) 2019 The University of Manchester
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
from typing import Any, Collection

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_machine import Chip
from spinn_machine.multicast_routing_entry import MulticastRoutingEntry
from pacman.data.pacman_data_view import PacmanDataView


class AbstractMulticastRoutingTable(object, metaclass=AbstractBase):
    """
    A multicast routing table. May be compressed or uncompressed.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def x(self) -> int:
        """
        The X-coordinate of the chip of this table.

        :rtype: int
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def y(self) -> int:
        """
        The Y-coordinate of the chip of this table.

        :rtype: int
        """
        raise NotImplementedError

    @property
    def chip(self) -> Chip:
        """
        The chip of this table.

        :rtype: ~spinn_machine.Chip
        """
        return PacmanDataView.get_chip_at(self.x, self.y)

    @property
    @abstractmethod
    def multicast_routing_entries(self) -> Collection[MulticastRoutingEntry]:
        """
        The multicast routing entries in the table.

        :rtype: iterable(~spinn_machine.MulticastRoutingEntry)
        """
        raise NotImplementedError

    @abstractmethod
    def add_multicast_routing_entry(
            self, multicast_routing_entry: MulticastRoutingEntry):
        """
        Adds a routing entry to this table.

        :param ~spinn_machine.MulticastRoutingEntry multicast_routing_entry:
            The route to add
        :raise PacmanAlreadyExistsException:
            If a routing entry with the same key-mask combination already
            exists
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def number_of_entries(self) -> int:
        """
        The number of multicast routing entries there are in the
        multicast routing table.

        :rtype: int
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def number_of_defaultable_entries(self) -> int:
        """
        The number of multicast routing entries that are set to be
        defaultable within this multicast routing table.

        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        """equals method"""
        raise NotImplementedError

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    @abstractmethod
    def __hash__(self) -> int:
        """hash"""
        raise NotImplementedError

    def __repr__(self) -> str:
        entry_string = "\n".join(
            str(entry) for entry in self.multicast_routing_entries)
        return f"{self.x}:{self.y}\n\n{entry_string}\n"
