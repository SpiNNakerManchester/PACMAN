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

from .application_spinnaker_link_vertex import ApplicationSpiNNakerLinkVertex
from pacman.model.graphs.application.abstract import Abstract2DDeviceVertex
from spinn_utilities.overrides import overrides


class Application2DSpiNNakerLinkVertex(
        ApplicationSpiNNakerLinkVertex, Abstract2DDeviceVertex):
    """
    """

    __slots__ = [
        "__width",
        "__height",
        "__sub_width",
        "__sub_height"
    ]

    def __init__(
            self, width, height, sub_width, sub_height,
            spinnaker_link_id, board_address=None, label=None,
            constraints=None, incoming=True, outgoing=False):
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
        :param iterable(AbstractConstraint) constraints:
            The optional initial constraints of the vertex.
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
        super(Application2DSpiNNakerLinkVertex, self).__init__(
            width * height, spinnaker_link_id, board_address,
            label, constraints, n_machine_vertices=self._n_sub_rectangles,
            incoming=incoming, outgoing=outgoing)
        self._verify_sub_size()

    @property
    @overrides(Abstract2DDeviceVertex._width)
    def _width(self):
        return self.__width

    @property
    @overrides(Abstract2DDeviceVertex._height)
    def _height(self):
        return self.__height

    @property
    @overrides(Abstract2DDeviceVertex._sub_width)
    def _sub_width(self):
        return self.__sub_width

    @property
    @overrides(Abstract2DDeviceVertex._sub_height)
    def _sub_height(self):
        return self.__sub_height

    @property
    @overrides(ApplicationSpiNNakerLinkVertex.atoms_shape)
    def atoms_shape(self):
        return (self.__width, self.__height)

    @overrides(ApplicationSpiNNakerLinkVertex.get_incoming_slice)
    def get_incoming_slice(self, index):
        return self._get_slice(index)
