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
from pacman.exceptions import PacmanConfigurationException
from spinn_utilities.abstract_base import abstractproperty


class AbstractMachineEdgePartition(object):
    """ A simple implementation of a machine edge partition that will \
        communicate with a traffic type.
    """

    __slots__ = ()

    def check_edge(self, edge):
        """ check a edge traffic type.

        :param AbstractEdge edge: the edge to check
        :raises PacmanInvalidParameterException:
            If the edge does not belong in this edge partition
        """
        # Check for an incompatible traffic type
        if edge.traffic_type != self.traffic_type:
            raise PacmanConfigurationException(
                "A partition can only contain edges with the same "
                "traffic_type; trying to add a {} edge to a partition of "
                "type {}".format(edge.traffic_type, self.traffic_type))

    @abstractproperty
    def traffic_type(self):
        """ The traffic type of all the edges in this edge partition.

        NOTE: the reason for a abstract property which all machine outgoing\
        partitions is purely due the need for multiple slots and pythons \
        lack of support for this.

        :rtype: EdgeTrafficType
        """
