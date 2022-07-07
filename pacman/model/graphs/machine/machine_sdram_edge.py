# Copyright (c) 2019-2020 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from pacman.model.graphs.machine import MachineEdge
from pacman.model.graphs import AbstractSupportsSDRAMEdges
from pacman.exceptions import PacmanConfigurationException


class SDRAMMachineEdge(MachineEdge):

    __slots__ = [
        # The sdram size of this edge.
        "_sdram_size",
        # The sdram base address for this edge
        "_sdram_base_address"
    ]

    def __init__(self, pre_vertex, post_vertex, label):
        if not isinstance(pre_vertex, AbstractSupportsSDRAMEdges):
            raise PacmanConfigurationException(
                f"Pre-vertex {pre_vertex} doesn't support SDRAM edges")
        super().__init__(pre_vertex, post_vertex, label=label)
        self._sdram_size = pre_vertex.sdram_requirement(self)
        self._sdram_base_address = None

    @property
    def sdram_size(self):
        return self._sdram_size

    @property
    def sdram_base_address(self):
        return self._sdram_base_address

    @sdram_base_address.setter
    def sdram_base_address(self, new_value):
        self._sdram_base_address = new_value

    def __repr__(self):
        return (f"SDRAMMachineEdge(pre_vertex={self.pre_vertex},"
                f" post_vertex={self.post_vertex}, label={self.label},"
                f" sdram_size={self.sdram_size})")

    def __str__(self):
        return self.__repr__()
