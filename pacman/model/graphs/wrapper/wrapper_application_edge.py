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

from pacman.model.graphs.application.application_edge import ApplicationEdge
from pacman.model.graphs.machine import MachineEdge, MachineVertex


class WrapperApplicationEdge(ApplicationEdge):

    __slots__ = []

    def __init__(self, edge):
        if type(edge) != MachineEdge:
            raise NotImplementedError(
                f"Unable to wrap edge of type {edge.__class__}")

        if isinstance(edge.pre_vertex, MachineVertex):
            pre_vertex = edge.pre_vertex.app_vertex
        else:
            pre_vertex = edge.pre_vertex
        if isinstance(edge.post_vertex, MachineVertex):
            post_vertex = edge.post_vertex.app_vertex
        else:
            post_vertex = edge.post_vertex

        super().__init__(pre_vertex, post_vertex, edge.label)
