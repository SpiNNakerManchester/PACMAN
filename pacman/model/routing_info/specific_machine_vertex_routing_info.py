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
from .machine_vertex_routing_info import MachineVertexRoutingInfo
if TYPE_CHECKING:
    from .base_key_and_mask import BaseKeyAndMask
    from pacman.model.graphs.machine import MachineVertex


class SpecificMachineVertexRoutingInfo(MachineVertexRoutingInfo):
    """
    Associates a machine vertex and partition identifier to its routing
    information (keys and masks).

    The global application mask is still used
    """

    __slots__ = (
        # The keys allocated to the machine partition
        "__machine_key_and_mask",)

    def __init__(self, key_and_mask: BaseKeyAndMask, partition_id: str,
                 machine_vertex: MachineVertex, index: int):
        """
        :param key_and_mask:
            The key allocated to the machine partition
        :param partition_id: The partition to set the keys for
        :param machine_vertex: The vertex to set the keys for
        :param index: The index of the machine vertex
        """
        super().__init__(partition_id, machine_vertex, index)
        self.__machine_key_and_mask = key_and_mask

    @property
    @overrides(MachineVertexRoutingInfo.key_and_mask)
    def key_and_mask(self) -> BaseKeyAndMask:
        return self.__machine_key_and_mask

    @property
    @overrides(MachineVertexRoutingInfo.app_mask)
    def app_mask(self) -> int:
        return self.get_global_application_mask()

    @property
    @overrides(MachineVertexRoutingInfo.machine_mask)
    def machine_mask(self) -> int:
        return self.__machine_key_and_mask.mask

    @property
    @overrides(MachineVertexRoutingInfo.has_global_masks)
    def has_global_masks(self) -> bool:
        return False

    @property
    @overrides(MachineVertexRoutingInfo.has_shiftable_masks)
    def has_shiftable_masks(self) -> bool:
        return True

    @property
    @overrides(MachineVertexRoutingInfo.has_fixed_keys)
    def has_fixed_keys(self) -> bool:
        return False
