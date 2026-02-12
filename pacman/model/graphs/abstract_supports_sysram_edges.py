# Copyright (c) 2020 The University of Manchester
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
from typing import TYPE_CHECKING
from spinn_utilities.abstract_base import abstractmethod, AbstractBase
if TYPE_CHECKING:
    from pacman.model.graphs.machine import SysRAMMachineEdge


# Can't use this decorator: circular import problem
# @require_subclass(MachineVertex)
class AbstractSupportsSysRAMEdges(object, metaclass=AbstractBase):
    """
    Marks a machine vertex that can have SysRAM edges attached to it.
    """

    __slots__ = ()

    @abstractmethod
    def sysram_requirement(
            self, sysram_machine_edge: SysRAMMachineEdge) -> int:
        """
        Asks a machine vertex for the SysRAM requirement it needs.

        :param sysram_machine_edge:
            The SysRAM edge in question
        :return: The size in bytes this vertex needs for the SysRAM edge.
        """
        raise NotImplementedError
