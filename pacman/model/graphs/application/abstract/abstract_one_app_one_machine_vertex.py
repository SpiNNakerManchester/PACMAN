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
from pacman.model.graphs.application import ApplicationVertex


class AbstractOneAppOneMachineVertex(ApplicationVertex):
    """ An ApplicationVertex that has a fixed Singleton MachineVertex
    """
    __slots__ = [
        # A pointer to the machine vertex set at init time
        "_machine_vertex"]

    def __init__(self, machine_vertex, label, constraints, n_atoms=1):
        """
        Creates an ApplicationVertex which has exactly one predefined \
        MachineVertex

        :param machine_vertex: MachineVertex
        :param str label: The optional name of the vertex.
        :param iterable(AbstractConstraint) constraints:
            The optional initial constraints of the vertex.
        :raise PacmanInvalidParameterException:
            If one of the constraints is not valid
        """
        super().__init__(label, constraints, n_atoms)
        self._machine_vertex = machine_vertex
        super().remember_machine_vertex(machine_vertex)

    @overrides(ApplicationVertex.remember_machine_vertex)
    def remember_machine_vertex(self, machine_vertex):
        assert (machine_vertex == self._machine_vertex)

    @property
    def machine_vertex(self):
        """
        Provides access to the MachineVertex at all times

        :rtype:  MachineVertex
        """
        return self._machine_vertex

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self):
        return self._machine_vertex.vertex_slice.n_atoms

    @overrides(ApplicationVertex.reset)
    def reset(self):
        # Override, as we don't want to clear the machine vertices here!
        if self._splitter is not None:
            self._splitter.reset_called()
