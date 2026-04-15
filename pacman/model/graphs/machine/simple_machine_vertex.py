# Copyright (c) 2016 The University of Manchester
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

from typing import Iterable, Optional

from spinn_utilities.overrides import overrides

from pacman.model.graphs.common import Slice
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.resources import AbstractSDRAM
from pacman.model.resources import IPtagResource
from pacman.model.resources import ReverseIPtagResource

from .machine_vertex import MachineVertex


class SimpleMachineVertex(MachineVertex):
    """
    A MachineVertex that stores its own resources.

    This class is mainly intended for JSON and testing as it support the
    minimal API. If a more complex Vertex is required consider the
    MockMachineVertex.
    """
    __slots__ = ("_iptags", "_reverse_iptags", "_sdram")

    def __init__(
            self, sdram: Optional[AbstractSDRAM], label: Optional[str] = None,
            app_vertex: Optional[ApplicationVertex] = None,
            vertex_slice: Optional[Slice] = None,
            iptags: Optional[Iterable[IPtagResource]] = None,
            reverse_iptags: Optional[Iterable[ReverseIPtagResource]] = None):
        """

        :param sdram: The SDRAM space required by the vertex.
        :param label: The optional name of the vertex
        :param app_vertex:
            The application vertex that caused this machine vertex to be
            created. If `None`, there is no such application vertex.
        :param vertex_slice:
            The slice of the application vertex that this machine vertex
            implements.
        :param iptags: The forward tags used by this vertex
        :param reverse_iptags: The reverse tags used by this vertex
        """
        super().__init__(
            label=label, app_vertex=app_vertex, vertex_slice=vertex_slice)
        self._sdram = sdram
        self._iptags: Iterable[IPtagResource] = []
        if iptags:
            self._iptags = iptags
        self._reverse_iptags: Iterable[ReverseIPtagResource] = []
        if reverse_iptags:
            self._reverse_iptags = reverse_iptags

    @property
    @overrides(MachineVertex.sdram_required)
    def sdram_required(self) -> AbstractSDRAM:
        assert self._sdram is not None
        return self._sdram

    @property
    @overrides(MachineVertex.iptags)
    def iptags(self) -> Iterable[IPtagResource]:
        return self._iptags

    @property
    @overrides(MachineVertex.reverse_iptags)
    def reverse_iptags(self) -> Iterable[ReverseIPtagResource]:
        return self._reverse_iptags
