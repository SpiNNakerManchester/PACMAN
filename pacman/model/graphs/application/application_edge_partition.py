# Copyright (c) 2017 The University of Manchester
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
from typing import TYPE_CHECKING
from spinn_utilities.overrides import overrides
from pacman.model.graphs import AbstractSingleSourcePartition
from .application_edge import ApplicationEdge
if TYPE_CHECKING:
    from .application_vertex import ApplicationVertex


class ApplicationEdgePartition(
        AbstractSingleSourcePartition['ApplicationVertex', ApplicationEdge]):
    """
    A simple implementation of an application edge partition that will
    communicate using SpiNNaker multicast packets. They have the same
    source(s) and semantics and so can share a single key.
    """

    __slots__ = ()

    def __init__(self, identifier: str, pre_vertex: ApplicationVertex):
        """
        :param identifier: The identifier of the partition
        :param pre_vertex: The source of this partition
        """
        super().__init__(
            pre_vertex=pre_vertex, identifier=identifier,
            allowed_edge_types=ApplicationEdge)

    @overrides(AbstractSingleSourcePartition.add_edge)
    def add_edge(self, edge: ApplicationEdge) -> None:
        super().add_edge(edge)
        edge.post_vertex.add_incoming_edge(edge, self)
