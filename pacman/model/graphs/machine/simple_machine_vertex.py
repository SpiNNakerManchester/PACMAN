# Copyright (c) 2017-2022 The University of Manchester
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

from .machine_vertex import MachineVertex
from spinn_utilities.overrides import overrides


class SimpleMachineVertex(MachineVertex):
    """ A MachineVertex that stores its own resources.

    This class is mainly intended for json and testing as it support the
        mininal API. If a more complex Vertex is required consider the
        MockMachineVertex.
    """
    __slots__ = ["_iptags", "_reverse_iptags", "_sdram"]

    def __init__(self, sdram, label=None, constraints=None,
                 app_vertex=None, vertex_slice=None, iptags=None,
                 reverse_iptags=None):
        super().__init__(
            label=label, constraints=constraints, app_vertex=app_vertex,
            vertex_slice=vertex_slice)
        self._sdram = sdram
        self._iptags = []
        if iptags:
            self._iptags = iptags
        self._reverse_iptags = []
        if reverse_iptags:
            self._reverse_iptags = reverse_iptags

    @property
    @overrides(MachineVertex.sdram_required)
    def sdram_required(self):
        return self._sdram

    @property
    @overrides(MachineVertex.iptags)
    def iptags(self):
        return self._iptags

    @property
    @overrides(MachineVertex.reverse_iptags)
    def reverse_iptags(self):
        return self._reverse_iptags
