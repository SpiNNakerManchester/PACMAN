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
from spinn_utilities.overrides import overrides
from .app_vertex_routing_info import AppVertexRoutingInfo
from .base_key_and_mask import BaseKeyAndMask

logger = logging.getLogger(__name__)


class GlobalAppVertexRoutingInfo(AppVertexRoutingInfo):
    """
    Routing information for an application vertex.
    """

    __slots__ = ()

    @property
    @overrides(AppVertexRoutingInfo.mask)
    def mask(self) -> int:
        return self.app_mask

    @property
    @overrides(AppVertexRoutingInfo.machine_mask)
    def machine_mask(self) -> int:
        return self.get_global_machine_mask()

    @property
    @overrides(AppVertexRoutingInfo.has_global_masks)
    def has_global_masks(self) -> bool:
        return True

    @property
    @overrides(AppVertexRoutingInfo.has_fixed_keys)
    def has_fixed_keys(self) -> bool:
        return False
