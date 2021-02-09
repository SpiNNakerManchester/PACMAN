# Copyright (c) 2020-2021 The University of Manchester
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
from spinn_utilities.abstract_base import abstractmethod, AbstractBase


# Can't use this decorator: circular import problem
# @require_subclass(MachineVertex)
class AbstractSupportsSDRAMEdges(object, metaclass=AbstractBase):

    __slots__ = []

    @abstractmethod
    def sdram_requirement(self, sdram_machine_edge):
        """ Asks a machine vertex for the sdram requirement it needs.

        :param sdram_machine_edge: The sdram edge in question
        :return: the size in bytes this sdram needs.
        :rtype: int (most likely a multiple of 4)
        """
