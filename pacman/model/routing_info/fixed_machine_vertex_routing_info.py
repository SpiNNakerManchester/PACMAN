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
from typing import Tuple, TYPE_CHECKING
from spinn_utilities.overrides import overrides

from pacman.utilities.constants import BITS_IN_KEY
from pacman.exceptions import IrregularFixedMaskException
from pacman.utilities.utility_calls import can_shift, signifacant_zone

from .machine_vertex_routing_info import MachineVertexRoutingInfo

if TYPE_CHECKING:
    from .base_key_and_mask import BaseKeyAndMask
    from pacman.model.graphs.machine import MachineVertex


class FixedMachineVertexRoutingInfo(MachineVertexRoutingInfo):
    """
    Associates a machine vertex and partition identifier to its routing
    information (keys and masks).
    """

    __slots__ = (
        # The mask allocated to the Application partition
        "__app_key_and_mask",
        # The keys allocated to the machine partition
        "__machine_key_and_mask")

    def __init__(self, key_and_mask: BaseKeyAndMask, partition_id: str,
                 machine_vertex: MachineVertex,
                 app_key_and_mask: BaseKeyAndMask, index: int):
        """
        :param key_and_mask:
            The key allocated to the machine partition
        :param partition_id: The partition to set the keys for
        :param machine_vertex: The vertex to set the keys for
        :param index: The index of the machine vertex
        """
        super().__init__(partition_id, machine_vertex, index)
        self.__app_key_and_mask = app_key_and_mask
        self.__machine_key_and_mask = key_and_mask

        if not can_shift(app_key_and_mask.mask):
            raise IrregularFixedMaskException(
                f"{machine_vertex} has a fixed app_mask "
                f"{hex(app_key_and_mask.mask)} which is not shiftable")
        elif not can_shift(key_and_mask.mask):
            raise IrregularFixedMaskException(
                f"{machine_vertex} has a fixed machine_mask "
                f"{hex(key_and_mask.mask)} which is not shiftable")
        else:
            if self.app_shift < self.machine_shift:
                raise IrregularFixedMaskException(
                    f"{machine_vertex} has a fixed app_mask "
                    f"{hex(app_key_and_mask.mask)} which is larger than "
                    f"fixed machine_mask {hex(key_and_mask.mask)}")

        # Currently we only support machine Zone == machine_index
        # If different is needed the MachineVertex will have to say so
        unshifted = self.key - app_key_and_mask.key
        shifted = unshifted >> self.machine_shift
        if self.index != shifted:
            raise IrregularFixedMaskException(
                f"{machine_vertex} has {index=} but "
                f"fixed key {hex(self.key)} - "
                f"fixed app key {hex(app_key_and_mask.key)} is "
                f"{hex(unshifted)} which shifted is {hex(shifted)}")

    @property
    @overrides(MachineVertexRoutingInfo.key_and_mask)
    def key_and_mask(self) -> BaseKeyAndMask:
        return self.__machine_key_and_mask

    @property
    @overrides(MachineVertexRoutingInfo.app_mask)
    def app_mask(self) -> int:
        return self.__app_key_and_mask.mask

    @property
    @overrides(MachineVertexRoutingInfo.machine_mask)
    def machine_mask(self) -> int:
        return self.__machine_key_and_mask.mask

    @property
    @overrides(MachineVertexRoutingInfo.has_global_masks)
    def has_global_masks(self) -> bool:
        # The allocator will try to use the fixed masks as the global ones
        return (self.app_mask == self.get_global_application_mask() and
                self.machine_mask == self.get_global_machine_mask())

    @property
    @overrides(MachineVertexRoutingInfo.has_fixed_keys)
    def has_fixed_keys(self) -> bool:
        return True

    def get_atom_bits_needed_range(self) -> Tuple[int, int]:
        app_key = self.__app_key_and_mask.key
        app_used = signifacant_zone(app_key)
        machine_index_key = self.key - app_key
        machine_used = signifacant_zone(machine_index_key)
        if app_used is None:
            min_needed = 0
        else:
            min_needed = app_used[1] + 1
        if machine_used is None:
            max_needed = BITS_IN_KEY - self.machine_shift
        else:
            max_needed = machine_used[0]
        return (min_needed, max_needed)
