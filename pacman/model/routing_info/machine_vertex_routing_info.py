# Copyright (c) 2021 The University of Manchester
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
from .vertex_routing_info import VertexRoutingInfo
from spinn_utilities.overrides import overrides


class MachineVertexRoutingInfo(VertexRoutingInfo):
    """ Associates a machine vertex and partition identifier to its routing
        information (keys and masks).
    """

    __slots__ = [

        # The machine vertex that the keys are allocated to
        "__machine_vertex",

        # The index of the machine vertex within the range of the application
        # vertex
        "__index"
    ]

    def __init__(self, keys_and_masks, partition_id, machine_vertex, index):
        """
        :param iterable(BaseKeyAndMask) keys_and_masks:\
            The keys allocated to the machine partition
        :param str partition_id: The partition to set the keys for
        :param MachineVertex machine_vertex: The vertex to set the keys for
        :param int index: The index of the machine vertex
        """
        super(MachineVertexRoutingInfo, self).__init__(
            keys_and_masks, partition_id)
        self.__machine_vertex = machine_vertex
        self.__index = index

    @property
    def machine_vertex(self):
        """ The machine vertex

        :rtype: MachineVertex
        """
        return self.__machine_vertex

    @property
    @overrides(VertexRoutingInfo.vertex)
    def vertex(self):
        return self.__machine_vertex

    @property
    def index(self):
        """ The index of the vertex
        """
        return self.__index
