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
from pacman.model.graphs import AbstractSupportsSDRAMEdges
from pacman.exceptions import PacmanConfigurationException
from .machine_vertex import MachineVertex


class SDRAMMachineEdge(MachineEdge):
    """
    An edge that transfers information via a shared SDRAM area. This implies
    that it must be between two machine vertices placed on the same chip.
    """

    __slots__ = (
        # The sdram size of this edge.
        "_sdram_size",
        # The sdram base address for this edge
        "_sdram_base_address")

    def __init__(
            self, pre_vertex: MachineVertex, post_vertex: MachineVertex,
            label: str):
        if not isinstance(pre_vertex, AbstractSupportsSDRAMEdges):
            raise PacmanConfigurationException(
                f"Pre-vertex {pre_vertex} doesn't support SDRAM edges")
        super().__init__(pre_vertex, post_vertex, label=label)
        self._sdram_size = pre_vertex.sdram_requirement(self)
        self._sdram_base_address: Optional[int] = None

    @property
    def sdram_size(self) -> int:
        """
        The sdram size reported by the pre_vertex

        :rtype: int
        """
        return self._sdram_size

    @property
    def sdram_base_address(self) -> Optional[int]:
        """
        The start address of the sdram if set

        :rtype: int or None
        """
        return self._sdram_base_address

    @sdram_base_address.setter
    def sdram_base_address(self, new_value: int):
        """
        Sets the start address without verification

        :param int new_value:
        """
        self._sdram_base_address = new_value

    def __repr__(self):
        return (f"SDRAMMachineEdge(pre_vertex={self.pre_vertex},"
                f" post_vertex={self.post_vertex}, label={self.label},"
                f" sdram_size={self.sdram_size})")

    def __str__(self):
        return self.__repr__()
