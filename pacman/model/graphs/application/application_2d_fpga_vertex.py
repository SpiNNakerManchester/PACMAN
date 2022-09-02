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
from pacman.model.graphs.common.slice import Slice


class Application2DFPGAVertex(ApplicationFPGAVertex, Abstract2DDeviceVertex):

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

    @overrides(ApplicationFPGAVertex.get_outgoing_slice)
    def get_outgoing_slice(self):
        return Slice(0, self.n_atoms - 1)
