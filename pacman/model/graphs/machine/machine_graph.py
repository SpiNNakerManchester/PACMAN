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
from .machine_edge import MachineEdge
from pacman.model.graphs import AbstractOutgoingEdgePartition
from pacman.model.graphs.impl import Graph


class MachineGraph(Graph):
    """ A graph whose vertices can fit on the chips of a machine.
    """

    __slots__ = []

    def __init__(self, label):
        super(MachineGraph, self).__init__(
            MachineVertex, MachineEdge, AbstractOutgoingEdgePartition, label)
