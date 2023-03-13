# Copyright (c) 2017 The University of Manchester
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

from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationVertex


class AbstractOneAppOneMachineVertex(ApplicationVertex):
    """ An ApplicationVertex that has a fixed singleton MachineVertex.
    """
    __slots__ = [
        # A pointer to the machine vertex set at init time
        "_machine_vertex"]

    def __init__(self, machine_vertex, label, n_atoms=1):
        """
        Creates an ApplicationVertex which has exactly one predefined
        MachineVertex.

        :param machine_vertex: MachineVertex
        :param str label: The optional name of the vertex.
        """
        super().__init__(label, n_atoms)
        self._machine_vertex = machine_vertex
        super().remember_machine_vertex(machine_vertex)

    @overrides(ApplicationVertex.remember_machine_vertex)
    def remember_machine_vertex(self, machine_vertex):
        assert (machine_vertex == self._machine_vertex)

    @property
    def machine_vertex(self):
        """
        Provides access to the MachineVertex at all times

        :rtype: MachineVertex
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
