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
    """ An association of a set of edges to a non-overlapping set of keys\
        and masks.
    """

    __slots__ = [
        # Partition information indexed by partition
        "_info_by_partition",

        # Partition information indexed by edge pre vertex and partition ID\
        # name
        "_info_by_prevertex",

        # Partition information by edge
        "_info_by_edge"
    ]

    def __init__(self, partition_info_items=None):
        """
        :param partition_info_items: The partition information items to add
        :type partition_info_items: iterable(PartitionRoutingInfo) or None
        :raise PacmanAlreadyExistsException: If there are
            two partition information objects with the same partition
        """

        # Partition information indexed by partition
        self._info_by_partition = dict()

        # Partition information indexed by edge pre vertex and partition ID
        # name
        self._info_by_prevertex = dict()

        # Partition information by edge
        self._info_by_edge = dict()

        if partition_info_items is not None:
            for partition_info_item in partition_info_items:
                self.add_partition_info(partition_info_item)

    def add_partition_info(self, partition_info):
        """ Add a partition information item

        :param PartitionRoutingInfo partition_info:\
            The partition information item to add
        :rtype: None
        :raise PacmanAlreadyExistsException:\
            If the partition is already in the set of edges
        """
        p = partition_info.partition

        if p in self._info_by_partition:
            raise PacmanAlreadyExistsException(
                "Partition", str(partition_info))
        if (p.pre_vertex, p.identifier) in self._info_by_prevertex:
            raise PacmanAlreadyExistsException(
                "Partition", str(partition_info))

        self._info_by_partition[p] = partition_info
        self._info_by_prevertex[p.pre_vertex, p.identifier] = partition_info

        for edge in p.edges:
            self._info_by_edge[edge] = partition_info

    def get_first_key_from_partition(self, partition):
        """ Get the first key associated with a particular partition

        :param AbstractSingleSourcePartition partition:\
            The partition to get the first key of
        :return: The routing key, or None if the partition does not exist
        :rtype: int or None
        """
        if partition in self._info_by_partition:
            return self._info_by_partition[
                partition].keys_and_masks[0].key
        return None

    def get_routing_info_from_partition(self, partition):
        """ Get the routing information for a given partition.

        :param AbstractSingleSourcePartition partition:\
            The partition to obtain routing information about.
        :return: the partition_routing_info for the partition, if any exists
        :rtype: PartitionRoutingInfo or None
        """
        if partition in self._info_by_partition:
            return self._info_by_partition[partition]
        return None

    def get_routing_info_from_pre_vertex(self, vertex, partition_id):
        """ Get routing information for edges with a given partition_id from\
            a prevertex

        :param AbstractVertex vertex: The prevertex to search for
        :param str partition_id:\
            The ID of the partition for which to get the routing information
        """
        if (vertex, partition_id) in self._info_by_prevertex:
            return self._info_by_prevertex[vertex, partition_id]
        return None

    def get_first_key_from_pre_vertex(self, vertex, partition_id):
        """ Get the first key for the partition starting at a (pre)vertex

        :param AbstractVertex vertex: The vertex which the partition starts at
        :param str partition_id:\
            The ID of the partition for which to get the routing information
        :return: The routing key of the partition
        :rtype: int
        """
        if (vertex, partition_id) in self._info_by_prevertex:
            return self._info_by_prevertex[
                vertex, partition_id].keys_and_masks[0].key
        return None

    def get_routing_info_for_edge(self, edge):
        """ Get routing information for an edge

        :param AbstractEdge edge: The edge to search for
        """
        return self._info_by_edge.get(edge, None)

    def get_first_key_for_edge(self, edge):
        """ Get routing key for an edge

        :param AbstractEdge edge: The edge to search for
        """
        if edge in self._info_by_edge:
            return self._info_by_edge[edge].keys_and_masks[0].key
        return None

    def __iter__(self):
        """ Gets an iterator for the partition routing information

        :return: a iterator of partition routing information
        """
        return iter(self._info_by_partition.values())
