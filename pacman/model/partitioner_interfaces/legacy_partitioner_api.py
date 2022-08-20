# Copyright (c) 2019-2022 The University of Manchester
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

from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


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
            self, vertex_slice, sdram, label=None, constraints=None):
        """ Create a machine vertex from this application vertex.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of atoms that the machine vertex will cover.
        :param ~pacman.model.resourcesAbstractSDRAM sdram:
            The sdram used by the machine vertex.
        :param label: human readable label for the machine vertex
        :type label: str or None
        :param constraints: Constraints to be passed on to the machine vertex.
        :type constraints:
            iterable(~pacman.model.constraints.AbstractConstraint)
        :return: The created machine vertex
        :rtype: ~pacman.model.graphs.machine.MachineVertex
        """

    @staticmethod
    def abstract_methods():
        """ Exposes the abstract methods and properties defined in this class.

        :rtype frozenset(str)
        """
        return LegacyPartitionerAPI.__abstractmethods__
