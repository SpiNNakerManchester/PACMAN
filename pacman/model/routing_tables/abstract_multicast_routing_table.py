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
from typing import Any, Iterable
from spinn_utilities.abstract_base import (
    AbstractBase, abstractproperty, abstractmethod)
from spinn_machine import Chip
from pacman.data.pacman_data_view import PacmanDataView
from spinn_machine.multicast_routing_entry import MulticastRoutingEntry


class AbstractMulticastRoutingTable(object, metaclass=AbstractBase):
    """
    A multicast routing table. May be compressed or uncompressed.
    """

    @abstractproperty
    def x(self) -> int:
        """
        The X-coordinate of the chip of this table.

        :rtype: int
        """

    @abstractproperty
    def y(self) -> int:
        """
        The Y-coordinate of the chip of this table.

        :rtype: int
        """

    @property
    def chip(self) -> Chip:
        """
        The chip of this table.

        :rtype: ~spinn_machine.Chip
        """
        return PacmanDataView.get_chip_at(self.x, self.y)

    @abstractproperty
    def multicast_routing_entries(self) -> Iterable[MulticastRoutingEntry]:
        """
        The multicast routing entries in the table.

        :rtype: iterable(~spinn_machine.MulticastRoutingEntry)
        """

    @abstractproperty
    def number_of_entries(self) -> int:
        """
        The number of multicast routing entries there are in the
        multicast routing table.

        :rtype: int
        """

    @abstractproperty
    def number_of_defaultable_entries(self) -> int:
        """
        The number of multicast routing entries that are set to be
        defaultable within this multicast routing table.

        :rtype: int
        """

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        """equals method"""

    @abstractmethod
    def __ne__(self, other: Any) -> bool:
        """ not equals method"""

    @abstractmethod
    def __hash__(self) -> int:
        """hash"""

    @abstractmethod
    def __repr__(self) -> str:
        """repr"""
