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

from typing import Optional, Tuple

from spinn_utilities.overrides import overrides

from pacman.model.graphs.application.abstract import Abstract2DDeviceVertex
from pacman.model.graphs.common import Slice

from .application_spinnaker_link_vertex import ApplicationSpiNNakerLinkVertex


class Application2DSpiNNakerLinkVertex(
        ApplicationSpiNNakerLinkVertex, Abstract2DDeviceVertex):
    """
    A 2D virtual application vertex that represents a device connected via a
    SpiNNaker link.
    """

    __slots__ = (
        "__width",
        "__height",
        "__sub_width",
        "__sub_height")

    def __init__(
            self, width: int, height: int, sub_width: int, sub_height: int,
            spinnaker_link_id: int, board_address: Optional[str] = None,
            label: Optional[str] = None,
            incoming: bool = True, outgoing: bool = False):
        """
        :param int width: The width of the vertex in atoms
        :param int height: The height of the vertex in atoms
        :param int sub_width:
            The width of the sub-rectangle to break the vertex up into
        :param int sub_height:
            The height of the sub-rectangle to break the vertex up into
        :param int spinnaker_link_id:
            The index of the spinnaker link to which the device is connected
        :param str board_address:
            The optional IP address of the board to which the device is
            connected e.g. in a multi-board system
        :param str label: The optional name of the vertex.
        :param bool incoming:
            Whether the device supports sending traffic into spinnaker
        :param bool outgoing:
            Whether the device supports receiving traffic from spinnaker
        """
        # Set variables first as this lets us call properties
        self.__width = width
        self.__height = height
        self.__sub_width = sub_width
        self.__sub_height = sub_height
        super().__init__(
            width * height, spinnaker_link_id, board_address,
            label, n_machine_vertices=self._n_sub_rectangles,
            incoming=incoming, outgoing=outgoing)
        self._verify_sub_size()

    @property
    @overrides(Abstract2DDeviceVertex.width)
    def width(self) -> int:
        return self.__width

    @property
    @overrides(Abstract2DDeviceVertex.height)
    def height(self) -> int:
        return self.__height

    @property
    @overrides(Abstract2DDeviceVertex.sub_width)
    def sub_width(self) -> int:
        return self.__sub_width

    @property
    @overrides(Abstract2DDeviceVertex.sub_height)
    def sub_height(self) -> int:
        return self.__sub_height

    @property
    @overrides(ApplicationSpiNNakerLinkVertex.atoms_shape)
    def atoms_shape(self) -> Tuple[int, ...]:
        return (self.__width, self.__height)

    @overrides(ApplicationSpiNNakerLinkVertex.get_incoming_slice)
    def get_incoming_slice(self, index: int) -> Slice:
        return self._get_slice(index)
