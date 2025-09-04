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
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from spinn_utilities.abstract_base import abstractmethod
from spinn_utilities.require_subclass import require_subclass
from pacman.model.graphs import AbstractVertex
if TYPE_CHECKING:
    from spinn_utilities.typing.coords import XY
    from spinn_machine import Machine
    from spinn_machine.link_data_objects import AbstractLinkData
    from pacman.model.routing_info import BaseKeyAndMask


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

    @property
    @abstractmethod
    def board_address(self) -> Optional[str]:
        """
        The IP address of the board to which the device is connected,
        or ``None`` for the boot board, or when using linked chip
        coordinates.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def linked_chip_coordinates(self) -> Optional[XY]:
        """
        The coordinates of the chip to which the device is connected,
        or ``None`` for the boot board, or when using a board address.
        """
        raise NotImplementedError

    @abstractmethod
    def outgoing_keys_and_masks(self) -> Optional[List[BaseKeyAndMask]]:
        """
        Get the keys sent by the device or `None` if there aren't any
        explicitly defined.

        :returns: The keys and masks used by the vertex if any
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def incoming(self) -> bool:
        """
        Whether this device sends traffic into SpiNNaker.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def outgoing(self) -> bool:
        """
        Whether this device receives traffic from SpiNNaker.
        """
        raise NotImplementedError

    @abstractmethod
    def get_link_data(self, machine: Machine) -> AbstractLinkData:
        """
        Get link data from the machine.

        :param machine: The machine to get the data from
        :returns: The link of the type used by the specific vertex.
        """
        raise NotImplementedError
