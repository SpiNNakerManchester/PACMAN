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

from spinn_utilities.overrides import overrides
from pacman.model.graphs.abstract_supports_sdram_edges import (
    AbstractSupportsSDRAMEdges)
from pacman.model.graphs.machine import SimpleMachineVertex


class MockMachineVertex(SimpleMachineVertex, AbstractSupportsSDRAMEdges):
    """ A MOCK MachineVertex used for tests with extra optional APIs

    This class is for tests where the SimpleMachineVertex is not enough.

    .. warning::
        This class may be extended to implement other Abstracts,
        so test can not depend on it failing an isinstance
    """

    def __init__(self, resources, label=None, constraints=None,
                 app_vertex=None, vertex_slice=None, sdram_requirement=None):
        """

        :param ~pacman.model.resources.ResourceContainer resources:
            The resources required by the vertex
        :type label: str or None
        :param iterable(AbstractConstraint) constraints:
            The optional initial constraints of the vertex
        :tpye constraints: iterable(AbstractConstraint)  or None
        :param app_vertex:
            The application vertex that caused this machine vertex to be
            created. If None, there is no such application vertex.
        :type app_vertex: ApplicationVertex or None
        :param vertex_slice:
            The slice of the application vertex that this machine vertex
            implements.
        :type vertex_slice: Slice or None
        :param sdram_requirement:
            Value to be returned by sdram_requirement method
            If None sdram_requirement method raises an exception
        :type sdram_requirement: int or None
        """
        super().__init__(resources, label=label, constraints=constraints,
            app_vertex=app_vertex, vertex_slice=vertex_slice)
        self._sdram_requirement = sdram_requirement

    @overrides(AbstractSupportsSDRAMEdges.sdram_requirement)
    def sdram_requirement(self, sdram_machine_edge):
        if self._sdram_requirement is None:
            raise NotImplementedError("No sdram_requirement supplied")
        return self._sdram_requirement
