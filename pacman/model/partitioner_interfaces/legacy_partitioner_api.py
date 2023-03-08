# Copyright (c) 2019 The University of Manchester
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

from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod)


# Can't use this decorator: circular import problem
# @require_subclass(ApplicationVertex)
class LegacyPartitionerAPI(object, metaclass=AbstractBase):
    """ API used by the vertices which dont have their own splitters but use\
        what master did before the self partitioning stuff came to be.
    """
    __slots__ = []

    @abstractmethod
    def get_sdram_used_by_atoms(self, vertex_slice):
        """ Get the separate sdram requirements for a range of atoms.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            the low value of atoms to calculate resources from
        :rtype: ~pacman.model.resources.AbstractSDRAM
        """

    @abstractmethod
    def create_machine_vertex(
            self, vertex_slice, sdram, label=None):
        """ Create a machine vertex from this application vertex.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of atoms that the machine vertex will cover.
        :param ~pacman.model.resourcesAbstractSDRAM sdram:
            The sdram used by the machine vertex.
        :param label: human readable label for the machine vertex
        :type label: str or None
        :return: The created machine vertex
        :rtype: ~pacman.model.graphs.machine.MachineVertex
        """

    @staticmethod
    def abstract_methods():
        """ Exposes the abstract methods and properties defined in this class.

        :rtype frozenset(str)
        """
        return LegacyPartitionerAPI.__abstractmethods__
