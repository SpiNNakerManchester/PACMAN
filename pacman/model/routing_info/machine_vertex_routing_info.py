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
from .vertex_routing_info import VertexRoutingInfo
from spinn_utilities.overrides import overrides


class MachineVertexRoutingInfo(VertexRoutingInfo):
    """
    Associates a machine vertex and partition identifier to its routing
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
        :param iterable(BaseKeyAndMask) keys_and_masks:
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
        """
        The machine vertex.

        :rtype: MachineVertex
        """
        return self.__machine_vertex

    @property
    @overrides(VertexRoutingInfo.vertex)
    def vertex(self):
        return self.__machine_vertex

    @property
    def index(self):
        """
        The index of the vertex.
        """
        return self.__index
