# Copyright (c) 2026 The University of Manchester
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
    from pacman.model.graphs.machine import MachineVertex
    from pacman.model.routing_info import BaseKeyAndMask


class SpecificMachineVertexRoutingInfo(MachineVertexRoutingInfo):
    """
    Associates a machine vertex and partition identifier to its routing
    information (keys and masks).

    The global Machine mask is not used,
    the global application mask is still used
    """

    __slots__ = (
        # The keys allocated to the machine partition
        "__global_machine_mask",)

    def __init__(self, key_and_mask: BaseKeyAndMask, partition_id: str,
                 machine_vertex: MachineVertex, index: int,
                 app_mask: int, global_machine_mask: int):
        """
        :param key_and_mask:
            The key and mask associated to the partition
        :param partition_id: The partition to set the keys for
        :param machine_vertex: The vertex to set the keys for
        :param index: The index of the machine vertex
        :param app_mask: The application mask
        :param global_machine_mask: The global machine mask
        """
        super().__init__(
            key_and_mask, partition_id, machine_vertex, index, app_mask)
        self.__global_machine_mask = global_machine_mask

    @property
    @overrides(MachineVertexRoutingInfo.has_global_app_masks)
    def has_global_app_masks(self) -> bool:
        return True

    @property
    @overrides(MachineVertexRoutingInfo.has_global_machine_masks)
    def has_global_machine_masks(self) -> bool:
        return False

    @property
    @overrides(MachineVertexRoutingInfo.has_app_keys_overlap)
    def has_app_keys_overlap(self) -> bool:
        return False

    @overrides(MachineVertexRoutingInfo.set_app_keys_overlap)
    def set_app_keys_overlap(self) -> None:
        raise NotImplementedError("Should never overlap")

    @property
    @overrides(MachineVertexRoutingInfo.has_fixed_keys)
    def has_fixed_keys(self) -> bool:
        return False

    @property
    @overrides(MachineVertexRoutingInfo.global_app_mask)
    def global_app_mask(self) -> int:
        return self.app_mask

    @property
    @overrides(MachineVertexRoutingInfo.global_machine_mask)
    def global_machine_mask(self) -> int:
        return self.__global_machine_mask
