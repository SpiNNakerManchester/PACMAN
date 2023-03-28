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

from spinn_utilities.abstract_base import (
    AbstractBase, abstractproperty, abstractmethod)


class AbstractMulticastRoutingTable(object, metaclass=AbstractBase):

    @abstractproperty
    def x(self):
        """
        The x-coordinate of the chip of this table.

        :return: The x-coordinate
        :rtype: int
        """

    @abstractproperty
    def y(self):
        """
        The y-coordinate of the chip of this table.

        :return: The y-coordinate
        :rtype: int
        """

    @abstractproperty
    def multicast_routing_entries(self):
        """
        The multicast routing entries in the table.

        :return: an iterable of multicast routing entries
        :rtype: iterable(~spinn_machine.MulticastRoutingEntry)
        """

    @abstractproperty
    def number_of_entries(self):
        """
        The number of multicast routing entries there are in the
        multicast routing table.

        :rtype: int
        """

    @abstractproperty
    def number_of_defaultable_entries(self):
        """
        The number of multicast routing entries that are set to be
        defaultable within this multicast routing table.

        :rtype: int
        """

    @abstractmethod
    def __eq__(self, other):
        """equals method"""

    @abstractmethod
    def __ne__(self, other):
        """ not equals method"""

    @abstractmethod
    def __hash__(self):
        """hash"""

    @abstractmethod
    def __repr__(self):
        """repr"""
