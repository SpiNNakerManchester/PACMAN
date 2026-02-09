# Copyright (c) 2019 The University of Manchester
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
from typing import Optional
from pacman.model.graphs.machine import MachineEdge
from pacman.model.graphs import AbstractSupportsSysRAMEdges
from pacman.exceptions import PacmanConfigurationException
from .machine_vertex import MachineVertex


class SysRAMMachineEdge(MachineEdge):
    """
    An edge that transfers information via a shared System RAM area.
    This implies that it must be between two machine vertices placed on the
    same chip.
    """

    __slots__ = (
        # The sysram size of this edge.
        "_sysram_size",
        # The sysram base address for this edge
        "_sysram_base_address")

    def __init__(
            self, pre_vertex: MachineVertex, post_vertex: MachineVertex,
            label: str):
        """
        :param pre_vertex: The vertex at the start of the edge.
        :param post_vertex: The vertex at the end of the edge.
        :param label: The name of the edge.
        """
        if not isinstance(pre_vertex, AbstractSupportsSysRAMEdges):
            raise PacmanConfigurationException(
                f"Pre-vertex {pre_vertex} doesn't support System RAM edges")
        super().__init__(pre_vertex, post_vertex, label=label)
        self._sysram_size = pre_vertex.sysram_requirement(self)
        self._sysram_base_address: Optional[int] = None

    @property
    def sysram_size(self) -> int:
        """
        The System RAM size reported by the pre_vertex
        """
        return self._sdram_size

    @property
    def sysram_base_address(self) -> Optional[int]:
        """
        The start address of the system RAM if set
        """
        return self._sysram_base_address

    @sysram_base_address.setter
    def sysram_base_address(self, new_value: int) -> None:
        """
        Sets the start address without verification

        :param new_value:
        """
        self._sdram_base_address = new_value

    def __repr__(self) -> str:
        return (f"SysRAMMachineEdge(pre_vertex={self.pre_vertex},"
                f" post_vertex={self.post_vertex}, label={self.label},"
                f" sdram_size={self.sdram_size})")

    def __str__(self) -> str:
        return self.__repr__()
