# Copyright (c) 2016 The University of Manchester
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

from spinn_utilities.abstract_base import abstractmethod, abstractproperty
from spinn_utilities.require_subclass import require_subclass
from pacman.model.graphs.abstract_vertex import AbstractVertex


@require_subclass(AbstractVertex)
class AbstractVirtual(object):
    """
    A vertex which exists outside of the machine,
    allowing a graph to formally participate in I/O.

    .. note::
        Everything that is an instance of ``AbstractVirtual`` is also an
        instance of :py:class:`~pacman.model.graphs.AbstractVertex`.
    """

    __slots__ = ()

    @abstractproperty
    def board_address(self):
        """
        The IP address of the board to which the device is connected,
        or ``None`` for the boot board, or when using linked chip
        coordinates.

        :rtype: str or None
        """

    @abstractproperty
    def linked_chip_coordinates(self):
        """
        The coordinates of the chip to which the device is connected,
        or ``None`` for the boot board, or when using a board address.

        :rtype: tuple(int, int) or None
        """

    @abstractmethod
    def outgoing_keys_and_masks(self):
        """
        Get the keys sent by the device or `None` if there aren't any
        explicitly defined.

        :rtype: list(~pacman.model.routing_info.BaseKeyAndMask) or None
        """

    @abstractproperty
    def incoming(self):
        """
        Whether this device sends traffic into SpiNNaker.

        :rtype: bool
        """

    @abstractproperty
    def outgoing(self):
        """
        Whether this device receives traffic from SpiNNaker.

        :rtype: bool
        """

    @abstractmethod
    def get_link_data(self, machine):
        """
        Get link data from the machine.

        :param ~spinn_machine.Machine machine:
            The machine to get the data from
        :rtype: ~spinn_machine.link_data_objects.AbstractLinkData
        """
