# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
            label=None):
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
        """
        # Set variables first as this lets us call properties
        self.__width = width
        self.__height = height
        self.__sub_width = sub_width
        self.__sub_height = sub_height
        super(Application2DFPGAVertex, self).__init__(
            width * height, incoming_fpga_connections,
            outgoing_fpga_connection, label,
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
