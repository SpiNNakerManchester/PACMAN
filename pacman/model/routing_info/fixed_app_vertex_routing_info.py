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
from .fixed_info import FixedInfo

if TYPE_CHECKING:
    from pacman.model.graphs.application import ApplicationVertex

logger = logging.getLogger(__name__)


class FixedAppVertexRoutingInfo(AppVertexRoutingInfo, FixedInfo):
    """
    Routing information for an application vertex with fixed keys
    """

    __slots__ = ()

    def __init__(
            self, key_and_mask: BaseKeyAndMask, partition_id: str,
            app_vertex: ApplicationVertex, machine_mask: int,
            n_bits_atoms: int, max_machine_index: int):
        """
        :param key_and_mask
        :param partition_id:
        :param app_vertex:
        :param machine_mask:
        :param n_bits_atoms:
        :param max_machine_index:
        """
        AppVertexRoutingInfo.__init__(key_and_mask.key, partition_id, app_vertex, machine_mask,
                         n_bits_atoms, max_machine_index)
        FixedInfo.__init__(key_and_mask.mask, machine_mask)
