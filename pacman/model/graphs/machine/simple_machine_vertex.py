# Copyright (c) 2017-2019 The University of Manchester
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
from ..abstract_supports_sdram_edges import AbstractSupportsSDRAMEdges


class SimpleMachineVertex(MachineVertex, AbstractSupportsSDRAMEdges):
    """ A MachineVertex that stores its own resources.
    """

    def __init__(self, resources, label=None, constraints=None,
                 app_vertex=None, vertex_slice=None, sdram_cost=0):
        super(SimpleMachineVertex, self).__init__(
            label=label, constraints=constraints, app_vertex=app_vertex,
            vertex_slice=vertex_slice)
        self._resources = resources
        self._sdram_cost = sdram_cost

    @property
    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return self._resources

    @overrides(AbstractSupportsSDRAMEdges.sdram_requirement)
    def sdram_requirement(self, sdram_machine_edge):
        return self._sdram_cost
