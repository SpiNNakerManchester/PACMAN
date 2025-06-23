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
from __future__ import annotations
from typing import Generic, Optional, TypeVar, TYPE_CHECKING
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationVertex
if TYPE_CHECKING:
    from pacman.model.graphs.machine import MachineVertex  # @UnusedImport
#: :meta private:
V = TypeVar("V", bound='MachineVertex')


class AbstractOneAppOneMachineVertex(ApplicationVertex, Generic[V]):
    """
    An application vertex that has a fixed singleton :py:class:`MachineVertex`.
    """
    __slots__ = (
        # A pointer to the machine vertex set at init time
        "_machine_vertex", )

    def __init__(self, machine_vertex: V, label: Optional[str],
                 n_atoms: int = 1):
        """
        :param machine_vertex: The fixed machine vertex.
        :param label: The optional name of the vertex.
        """
        super().__init__(label, n_atoms)
        self._machine_vertex = machine_vertex
        super().remember_machine_vertex(machine_vertex)

    @overrides(ApplicationVertex.remember_machine_vertex)
    def remember_machine_vertex(self, machine_vertex: V) -> None:
        assert (machine_vertex == self._machine_vertex)

    @property
    def machine_vertex(self) -> V:
        """
        Provides access to the machine vertex at all times
        """
        return self._machine_vertex

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self) -> int:
        return self._machine_vertex.vertex_slice.n_atoms

    @overrides(ApplicationVertex.reset)
    def reset(self) -> None:
        # Override, as we don't want to clear the machine vertices here!
        if self._splitter is not None:
            self._splitter.reset_called()
