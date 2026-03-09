# Copyright (c) 2021 The University of Manchester
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
import logging
from typing import TYPE_CHECKING
from spinn_utilities.overrides import overrides
from pacman.utilities.utility_calls import can_shift, calc_shift
from .app_vertex_routing_info import AppVertexRoutingInfo
from .base_key_and_mask import BaseKeyAndMask

if TYPE_CHECKING:
    from pacman.model.graphs.application import ApplicationVertex

logger = logging.getLogger(__name__)


class FixedAppVertexRoutingInfo(AppVertexRoutingInfo):
    """
    Routing information for an application vertex with fixed keys
    """

    __slots__ = (
        # The mask allocated to the Application partition
        "__app_mask",
        # The mask allocated to the machine (plus application) partition
        "__machine_mask",
        # cached value for shiftable
        "__shiftable"
    )

    def __init__(
            self, key_and_mask: BaseKeyAndMask, partition_id: str,
            app_vertex: ApplicationVertex, machine_mask: int,
            max_machine_index: int):
        """
        :param key_and_mask
        :param partition_id:
        :param app_vertex:
        :param machine_mask:
        :param max_machine_index:
        """
        super().__init__(key_and_mask.key, partition_id, app_vertex,
                         max_machine_index)
        self.__app_mask = key_and_mask.mask
        self.__machine_mask = machine_mask
        if not can_shift(self.__app_mask):
            self.__shiftable = False
        elif not can_shift(machine_mask):
            self.__shiftable = False
        else:
            self.__shiftable = (
                calc_shift(self.__app_mask) >= calc_shift(machine_mask))

    @property
    @overrides(AppVertexRoutingInfo.key_and_mask)
    def key_and_mask(self) -> BaseKeyAndMask:
        return BaseKeyAndMask(
            self._app_key, self.__app_mask)

    @property
    @overrides(AppVertexRoutingInfo.app_mask)
    def app_mask(self) -> int:
        return self.__app_mask

    @property
    @overrides(AppVertexRoutingInfo.machine_mask)
    def machine_mask(self) -> int:
        return self.__machine_mask

    @property
    @overrides(AppVertexRoutingInfo.has_global_masks)
    def has_global_masks(self) -> bool:
        # The allocator will try to use the fixed masks as the global ones
        return (self.__app_mask == self.get_global_application_mask() and
                self.__machine_mask == self.get_global_machine_mask())

    @property
    @overrides(AppVertexRoutingInfo.has_shiftable_masks)
    def has_shiftable_masks(self) -> bool:
        return self.__shiftable

    @property
    @overrides(AppVertexRoutingInfo.has_fixed_keys)
    def has_fixed_keys(self) -> bool:
        return True
