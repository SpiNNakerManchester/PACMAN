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
from typing import TYPE_CHECKING
from spinn_utilities.overrides import overrides
from .vertex_routing_info import VertexRoutingInfo
if TYPE_CHECKING:
    from .base_key_and_mask import BaseKeyAndMask
    from pacman.model.graphs.machine import MachineVertex


class MachineVertexRoutingInfo(VertexRoutingInfo):
    """
    Associates a machine vertex and partition identifier to its routing
    information (keys and masks).
    """

    __slots__ = (
        # The machine vertex that the keys are allocated to
        "__machine_vertex",

        # The index of the machine vertex within the range of the application
        # vertex
        "__index")

    def __init__(self, key_and_mask: BaseKeyAndMask, partition_id: str,
                 machine_vertex: MachineVertex, index: int):
        """
        :param BaseKeyAndMask key_and_mask:
            The key allocated to the machine partition
        :param str partition_id: The partition to set the keys for
        :param MachineVertex machine_vertex: The vertex to set the keys for
        :param int index: The index of the machine vertex
        """
        super().__init__(key_and_mask, partition_id)
        self.__machine_vertex = machine_vertex
        self.__index = index

    @property
    def machine_vertex(self) -> MachineVertex:
        """
        The machine vertex.

        :rtype: MachineVertex
        """
        return self.__machine_vertex

    @property
    @overrides(VertexRoutingInfo.vertex)
    def vertex(self) -> MachineVertex:
        return self.__machine_vertex

    @property
    def index(self) -> int:
        """
        The index of the vertex.

        :rtype: int
        """
        return self.__index
