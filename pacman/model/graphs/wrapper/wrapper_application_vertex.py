# Copyright (c) 2022-202 The University of Manchester
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

from pacman.exceptions import PacmanInvalidParameterException
from pacman.model.graphs.abstract_supports_sdram_edges import (
    AbstractSupportsSDRAMEdges)
from pacman.model.graphs.abstract_virtual import AbstractVirtual
from pacman.model.graphs.application.abstract import (
    AbstractOneAppOneMachineVertex)
from pacman.model.graphs.machine import MachineVertex


class WrapperApplicationVertex(AbstractOneAppOneMachineVertex):

    def __init__(self, vertex):
        """
        Creates an ApplicationVertex which has exactly one predefined \
        MachineVertex

        :param MachineVertex vertex: MachineVertex
        :param iterable(AbstractConstraint) constraints:
            The optional initial constraints of the vertex.
        :raise PacmanInvalidParameterException:
            If one of the constraints is not valid
        """
        if not isinstance(vertex, MachineVertex):
            raise PacmanInvalidParameterException(
                "vertex", str(vertex.__class__),
                "Can only wrap MachineVertex")
        if isinstance(vertex, AbstractSupportsSDRAMEdges):
            raise NotImplementedError(
                "Wrapping a vertex which implements "
                "AbstractSupportsSDRAMEdges is not supported yet")
        if isinstance(vertex, AbstractVirtual):
            raise NotImplementedError(
                "Wrapping a virtual vertex is not supported yet")
        super().__init__(
            vertex, vertex.label, None, vertex.vertex_slice.n_atoms)
        vertex._app_vertex = self

    def __repr__(self):
        if self.constraints:
            return f"Wrapped Vertex(label={self.label}, " \
                   f"constraints={self.constraints}"
        else:
            return f"Wrapped Vertex(label={self.label}"
