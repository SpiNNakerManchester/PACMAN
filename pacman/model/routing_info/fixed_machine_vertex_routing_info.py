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
from pacman.utilities.utility_calls import (
    calc_shift, can_shift, signifacant_zone)

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
        elif not can_shift(key_and_mask.mask):
            raise IrregularFixedMaskException(
                f"{machine_vertex} has a fixed machine_mask "
                f"{hex(key_and_mask.mask)} which is not shiftable")
        else:
            # Do not use the global as not yet set
            app_shift = calc_shift(app_key_and_mask.mask)
            if app_shift < self.machine_shift:
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
