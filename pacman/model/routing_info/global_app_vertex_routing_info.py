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
from spinn_utilities.overrides import overrides
from .app_vertex_routing_info import AppVertexRoutingInfo

logger = logging.getLogger(__name__)


class GlobalAppVertexRoutingInfo(AppVertexRoutingInfo):
    """
    Routing information for an application vertex.

    This info come from a Vertex without fixed keys
    """

    __slots__ = ()

    @property
    @overrides(AppVertexRoutingInfo.has_global_app_masks)
    def has_global_app_masks(self) -> bool:
        return True

    @property
    @overrides(AppVertexRoutingInfo.has_global_machine_masks)
    def has_global_machine_masks(self) -> bool:
        return True

    @property
    @overrides(AppVertexRoutingInfo.has_app_keys_overlap)
    def has_app_keys_overlap(self) -> bool:
        return False

    @overrides(AppVertexRoutingInfo.set_app_keys_overlap)
    def set_app_keys_overlap(self) -> None:
        raise NotImplementedError("Should never overlap")

    @property
    @overrides(AppVertexRoutingInfo.has_fixed_keys)
    def has_fixed_keys(self) -> bool:
        return False

    @property
    @overrides(AppVertexRoutingInfo.global_app_mask)
    def global_app_mask(self) -> int:
        return self.mask

    @property
    @overrides(AppVertexRoutingInfo.global_machine_mask)
    def global_machine_mask(self) -> int:
        return self.machine_mask
