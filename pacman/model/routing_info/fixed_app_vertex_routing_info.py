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

import logging
from typing import TYPE_CHECKING, Optional

from spinn_utilities.overrides import overrides

from pacman.exceptions import IrregularFixedMaskException
from pacman.utilities.utility_calls import can_shift

from .app_vertex_routing_info import AppVertexRoutingInfo
from .base_key_and_mask import BaseKeyAndMask

if TYPE_CHECKING:
    from pacman.model.graphs.application import ApplicationVertex

logger = logging.getLogger(__name__)


class FixedAppVertexRoutingInfo(AppVertexRoutingInfo):
    """
    Routing information for an application vertex with fixed keys and masks

    This class is used even if the fixed masks are the global ones.
    """

    __slots__ = (
        # Records this has app keys overlap
        "__app_key_overlap",
        "__global_app_mask",
        "__global_machine_mask"
    )

    def __init__(
            self, key_and_mask: BaseKeyAndMask, partition_id: str,
            app_vertex: ApplicationVertex,
            max_machine_index: int, machine_mask: int):
        """
        :param key_and_mask
        :param partition_id:
        :param app_vertex:
        :param machine_mask:
        :param max_machine_index:
        """
        super().__init__(key_and_mask, partition_id, app_vertex,
                         max_machine_index, machine_mask)
        self.__app_key_overlap = False
        self.__global_app_mask: Optional[int] = None
        self.__global_machine_mask: Optional[int] = None

        if not can_shift(key_and_mask.mask):
            raise IrregularFixedMaskException(
                f"{app_vertex} has a fixed app mask {key_and_mask.mask} "
                f"which is not shiftable")

    @property
    @overrides(AppVertexRoutingInfo.has_global_app_masks)
    def has_global_app_masks(self) -> bool:
        return self.mask == self.global_app_mask

    @property
    @overrides(AppVertexRoutingInfo.has_global_machine_masks)
    def has_global_machine_masks(self) -> bool:
        return self.machine_mask == self.global_machine_mask

    @property
    @overrides(AppVertexRoutingInfo.has_app_keys_overlap)
    def has_app_keys_overlap(self) -> bool:
        return self.__app_key_overlap

    @overrides(AppVertexRoutingInfo.set_app_keys_overlap)
    def set_app_keys_overlap(self) -> None:
        self.__app_key_overlap = True

    @property
    @overrides(AppVertexRoutingInfo.has_fixed_keys)
    def has_fixed_keys(self) -> bool:
        return True

    @overrides(AppVertexRoutingInfo.set_global_masks)
    def set_global_masks(self, app_mask: int, machine_mask: int) -> None:
        self.__global_app_mask = app_mask
        self.__global_machine_mask = machine_mask

    @property
    @overrides(AppVertexRoutingInfo.global_app_mask)
    def global_app_mask(self) -> int:
        if self.__global_app_mask is None:
            raise IrregularFixedMaskException("No global app mask set")
        return self.__global_app_mask

    @property
    @overrides(AppVertexRoutingInfo.global_machine_mask)
    def global_machine_mask(self) -> int:
        if self.__global_machine_mask is None:
            raise IrregularFixedMaskException("No global machine mask set")
        return self.__global_machine_mask
