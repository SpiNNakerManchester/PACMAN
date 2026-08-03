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

from typing import TYPE_CHECKING, Optional, Tuple

from spinn_utilities.overrides import overrides

from pacman.exceptions import IrregularFixedMaskException
from pacman.utilities.constants import BITS_IN_KEY
from pacman.utilities.utility_calls import can_shift, first_one, last_one

from .machine_vertex_routing_info import MachineVertexRoutingInfo

if TYPE_CHECKING:
    from pacman.model.graphs.machine import MachineVertex

    from .base_key_and_mask import BaseKeyAndMask


class FixedMachineVertexRoutingInfo(MachineVertexRoutingInfo):
    """
    Associates a machine vertex and partition identifier to its routing
    information (keys and masks).

    This is used then the Vertex has fixed masks
    even if they are the global ones.
    """

    __slots__ = (
        # Records this has app keys overlap
        "__app_key_overlap",
        "__app_key",
        "__global_app_mask",
        "__global_machine_mask"
    )

    def __init__(self, key_and_mask: BaseKeyAndMask, partition_id: str,
                 machine_vertex: MachineVertex, index: int,
                 app_key_and_mask: BaseKeyAndMask):
        """
        :param key_and_mask:
            The key and mask associated to the partition
        :param partition_id: The partition to set the keys for
        :param machine_vertex: The vertex to set the keys for
        :param index: The index of the machine vertex
        :param app_key_and_mask: The application key and mask
        """
        super().__init__(key_and_mask, partition_id, machine_vertex, index,
                         app_key_and_mask.mask)
        self.__app_key_overlap = False
        self.__app_key = app_key_and_mask.key
        self.__global_app_mask: Optional[int] = None
        self.__global_machine_mask: Optional[int] = None

        if not can_shift(app_key_and_mask.mask):
            raise IrregularFixedMaskException(
                f"{machine_vertex} has a fixed app_mask "
                f"{hex(app_key_and_mask.mask)} which is not shiftable")

    @property
    @overrides(MachineVertexRoutingInfo.has_global_app_masks)
    def has_global_app_masks(self) -> bool:
        # The allocator will try to use the fixed masks as the global ones
        return self.app_mask == self.global_app_mask

    @property
    @overrides(MachineVertexRoutingInfo.has_global_machine_masks)
    def has_global_machine_masks(self) -> bool:
        # The allocator will try to use the fixed masks as the global ones
        return self.machine_mask == self.global_machine_mask

    @property
    @overrides(MachineVertexRoutingInfo.has_app_keys_overlap)
    def has_app_keys_overlap(self) -> bool:
        return self.__app_key_overlap

    @overrides(MachineVertexRoutingInfo.set_app_keys_overlap)
    def set_app_keys_overlap(self) -> None:
        self.__app_key_overlap = True

    @property
    @overrides(MachineVertexRoutingInfo.has_fixed_keys)
    def has_fixed_keys(self) -> bool:
        return True

    def get_atom_bits_needed_range(self) -> Tuple[int, int]:
        """
        The range of atom bit values that this info can support.

        Based on the Application and Machine keys it may be able to alter the
        Application Mask without changing now results.

        The number of atom bits will be large enough
        to not blank out any ones in the application key
        but also small enough to blank out the machine index.
        (The part of the Machine key that are not also application key)

        :return: Smallest and largest application zone supportable
        """
        # If app and machine the same allow the split anywhere
        if (self.machine_mask == self.app_mask and
                self.key == self.__app_key):
            return 0, BITS_IN_KEY - self.machine_shift

        last_app_one = last_one(self.__app_key)
        machine_index_bit = self.key - self.__app_key
        first_machine_one = first_one(machine_index_bit)
        if first_machine_one == -1:
            return last_app_one + 1, BITS_IN_KEY
        else:
            return last_app_one + 1, first_machine_one

    @overrides(MachineVertexRoutingInfo.set_global_masks)
    def set_global_masks(self, app_mask: int, machine_mask: int) -> None:
        self.__global_app_mask = app_mask
        self.__global_machine_mask = machine_mask

    @property
    @overrides(MachineVertexRoutingInfo.global_app_mask)
    def global_app_mask(self) -> int:
        if self.__global_app_mask is None:
            raise IrregularFixedMaskException("No global app mask set")
        return self.__global_app_mask

    @property
    @overrides(MachineVertexRoutingInfo.global_machine_mask)
    def global_machine_mask(self) -> int:
        if self.__global_machine_mask is None:
            raise IrregularFixedMaskException("No global machine mask set")
        return self.__global_machine_mask
