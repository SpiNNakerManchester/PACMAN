# Copyright (c) 2019-2020 The University of Manchester
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
from six import add_metaclass
from spinn_utilities.abstract_base import abstractmethod, AbstractBase


@add_metaclass(AbstractBase)
class AbstractApplicationOutgoingPartition(object):

    @abstractmethod
    def convert_to_machine_out_going_partition(self, machine_pre_vertex):
        """ Build an equivalent of this application outgoing partition as a\
            machine outgoing partition.

        :param MachineVertex machine_pre_vertex:
            the machine vertex to be the pre-vertex
        :return: The machine outgoing partition
        :rtype: AbstractEdgePartition
        """
