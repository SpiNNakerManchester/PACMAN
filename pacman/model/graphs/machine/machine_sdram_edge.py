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


from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine import MachineEdge


class SDRAMMachineEdge(MachineEdge):

    __slots__ = [
        "_sdram_size",
        "_sdram_base_address"

    ]

    def __init__(self, pre_vertex, post_vertex, sdram_size, label):
        MachineEdge.__init__(
            self, pre_vertex, post_vertex, traffic_type=EdgeTrafficType.SDRAM,
            label=label, traffic_weight=1)
        self._sdram_size = sdram_size
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
        return self._label

    def __str__(self):
        return self.__repr__()
