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

from spinn_utilities.overrides import overrides
from pacman.utilities.utility_calls import can_shift, calc_shift
from .vertex_routing_info import VertexRoutingInfo

class FixedInfo(object):
    """
    Indicates an Info that was created using fixed keys
    """

    __slots__ = (
        # The mask allocated to the Application partition
        "__app_mask",
        # The mask allocated to the machine (plus application) partition
        "__machine_mask",
        "__shiftable"
    )

    def __init__(self, app_mask: int, machine_mask: int):
        self.__app_mask = app_mask
        self.__machine_mask = machine_mask
        if not can_shift(app_mask):
            self.__shiftable = False
        elif not can_shift(machine_mask):
            self.__shiftable = False
        else:
            self.__shiftable == (
                calc_shift(app_mask) <= calc_shift(machine_mask))

    @overrides(VertexRoutingInfo.app_mask)
    def app_mask(self) -> int:
        return self.__app_mask

    @overrides(VertexRoutingInfo.machine_mask)
    def machine_mask(self) -> int:
        return self.__machine_mask

    @overrides(VertexRoutingInfo.has_global_masks)
    def has_global_masks(self) -> bool:
        # The allocator will try to use the fixed masks as the global ones
        return (self.__app_mask == self.global_application_mask and
                self.machine_mask == self.global_machine_mask)

    @overrides(VertexRoutingInfo.has_shiftable_masks)
    def has_shiftable_masks(self) -> bool:
        return self.__shiftable

    @overrides(VertexRoutingInfo.has_fixed_keys)
    def has_fixed_keys(self) -> bool:
        return True
