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

from pacman.exceptions import PacmanAlreadyExistsException


class RoutingInfo(object):
    """ An association of machine vertices to a non-overlapping set of keys\
        and masks.
    """

    __slots__ = [

        # Partition information indexed by edge pre vertex and partition ID\
        # name
        "_info_by_prevertex"
    ]

    def __init__(self, items=None):
        """
        :param items: The routing info items to add
        :type items: iterable(MachineVertexRoutingInfo) or None
        :raise PacmanAlreadyExistsException: If there are
            two information objects with the same source
        """

        # Partition information indexed by edge pre vertex and partition ID
        # name
        self._info_by_prevertex = dict()

        if items is not None:
            for item in items:
                self.add_routing_info(item)

    def add_routing_info(self, info):
        """ Add a routing information item

        :param MachineVertexRoutingInfo info:
            The routing information item to add
        :rtype: None
        :raise PacmanAlreadyExistsException:
            If the partition is already in the set of edges
        """
        key = (info.vertex, info.partition_id)
        if key in self._info_by_prevertex:
            raise PacmanAlreadyExistsException(
                "Routing information", str(info))

        self._info_by_prevertex[key] = info

    def get_routing_info_from_pre_vertex(self, vertex, partition_id):
        """ Get routing information for a given partition_id from a vertex

        :param AbstractVertex vertex: The vertex to search for
        :param str partition_id:\
            The ID of the partition for which to get the routing information
        """
        return self._info_by_prevertex.get((vertex, partition_id))

    def get_first_key_from_pre_vertex(self, vertex, partition_id):
        """ Get the first key for the partition starting at a vertex

        :param MachineVertex vertex: The vertex which the partition starts at
        :param str partition_id:\
            The ID of the partition for which to get the routing information
        :return: The routing key of the partition
        :rtype: int
        """
        key = (vertex, partition_id)
        if key in self._info_by_prevertex:
            return self._info_by_prevertex[key].keys_and_masks[0].key
        return None

    def __iter__(self):
        """ Gets an iterator for the routing information

        :return: a iterator of routing information
        """
        return iter(self._info_by_prevertex.values())
