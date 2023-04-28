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
from spinn_utilities.abstract_base import abstractmethod, AbstractBase


# Can't use this decorator: circular import problem
# @require_subclass(MachineVertex)
class AbstractSupportsSDRAMEdges(object, metaclass=AbstractBase):
    """
    Marks a machine vertex that can have SDRAM edges attached to it.
    """

    __slots__ = []

    @abstractmethod
    def sdram_requirement(self, sdram_machine_edge):
        """
        Asks a machine vertex for the SDRAM requirement it needs.

        :param sdram_machine_edge:
            The SDRAM edge in question
        :type sdram_machine_edge:
            ~pacman.model.graphs.machine.SDRAMMachineEdge
        :return: The size in bytes this vertex needs for the SDRAM edge.
        :rtype: int (most likely a multiple of 4)
        """
