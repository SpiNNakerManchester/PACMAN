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

from .application_fpga_vertex import ApplicationFPGAVertex
from pacman.model.graphs.application.abstract import Abstract2DDeviceVertex
from spinn_utilities.overrides import overrides


class Application2DFPGAVertex(ApplicationFPGAVertex, Abstract2DDeviceVertex):
    """ A device connected to an FPGA with input or output in two dimensions
    """

    __slots__ = [
        "__width",
        "__height",
        "__sub_width",
        "__sub_height"
    ]

    def __init__(
            self, width, height, sub_width, sub_height,
            incoming_fpga_connections=None, outgoing_fpga_connection=None,
            label=None, constraints=None):
        """

        :param int width: The width of the vertex in atoms
        :param int height: The height of the vertex in atoms
        :param int sub_width:
            The width of the sub-rectangle to break the vertex up into
        :param int sub_height:
            The height of the sub-rectangle to break the vertex up into
        :param incoming_fpga_connections:
            The connections from one or more FPGAs that that packets are
            expected to be received from for this device, or None if no
            incoming traffic is expected from the device
        :type incoming_fpga_connections: list(FPGAConnection) or None
        :param outgoing_fpga_connection:
            The connection to an FPGA that packets to be sent to this device
            should be sent down, or None if no outgoing traffic is expected to
            be sent to the device.
        :type outgoing_fpga_connection: FPGAConnection or None
        :param str label: The optional name of the vertex.
        :param iterable(AbstractConstraint) constraints:
            The optional initial constraints of the vertex.
        """
        # Set variables first as this lets us call properties
        self.__width = width
        self.__height = height
        self.__sub_width = sub_width
        self.__sub_height = sub_height
        super(Application2DFPGAVertex, self).__init__(
            width * height, incoming_fpga_connections,
            outgoing_fpga_connection, label, constraints,
            n_machine_vertices_per_link=self._n_sub_rectangles)
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
    @overrides(ApplicationFPGAVertex.atoms_shape)
    def atoms_shape(self):
        return (self.__width, self.__height)

    @overrides(ApplicationFPGAVertex.get_incoming_slice_for_link)
    def get_incoming_slice_for_link(self, link, index):
        return self._get_slice(index)
