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
from typing import Tuple, TYPE_CHECKING
from spinn_utilities.overrides import overrides

from pacman.utilities.constants import BITS_IN_KEY
from pacman.exceptions import IrregularFixedMaskException
from pacman.utilities.utility_calls import can_shift, first_one, last_one

from .machine_vertex_routing_info import MachineVertexRoutingInfo

if TYPE_CHECKING:
    from .base_key_and_mask import BaseKeyAndMask
    from pacman.model.graphs.machine import MachineVertex


class FixedMachineVertexRoutingInfo(MachineVertexRoutingInfo):
    """
    Associates a machine vertex and partition identifier to its routing
    information (keys and masks).

    This is used then the Vertex has fixed masks
    even if they are the global ones.
    """

    __slots__ = (
        # The mask allocated to the Application partition
        "__app_key_and_mask",
        # The mask allocated to the machine partition
        "__machine_mask",
        # Records this has app keys overlap
        "__app_key_overlap")

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
        super().__init__(key_and_mask.key, partition_id, machine_vertex, index)
        self.__app_key_and_mask = app_key_and_mask
        self.__machine_mask = key_and_mask.mask
        self.__app_key_overlap = False

        if not can_shift(app_key_and_mask.mask):
            raise IrregularFixedMaskException(
                f"{machine_vertex} has a fixed app_mask "
                f"{hex(app_key_and_mask.mask)} which is not shiftable")

    @property
    @overrides(MachineVertexRoutingInfo.mask)
    def mask(self) -> int:
        return self.__machine_mask

    @property
    @overrides(MachineVertexRoutingInfo.app_mask)
    def app_mask(self) -> int:
        return self.__app_key_and_mask.mask

    @property
    @overrides(MachineVertexRoutingInfo.machine_mask)
    def machine_mask(self) -> int:
        return self.__machine_mask

    @property
    @overrides(MachineVertexRoutingInfo.has_global_app_masks)
    def has_global_app_masks(self) -> bool:
        # The allocator will try to use the fixed masks as the global ones
        return self.__app_key_and_mask.mask == self._global_application_mask

    @property
    @overrides(MachineVertexRoutingInfo.has_global_machine_masks)
    def has_global_machine_masks(self) -> bool:
        # The allocator will try to use the fixed masks as the global ones
        return self.__machine_mask == self._global_machine_mask

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
        if (self.__machine_mask == self.__app_key_and_mask.mask and
                self.key == self.__app_key_and_mask.key):
            return 0, BITS_IN_KEY - self.machine_shift

        app_key = self.__app_key_and_mask.key
        last_app_one = last_one(app_key)
        machine_index_bit = self.key - app_key
        first_machine_one = first_one(machine_index_bit)
        if first_machine_one == -1:
            return last_app_one + 1, BITS_IN_KEY
        else:
            return last_app_one + 1, first_machine_one
