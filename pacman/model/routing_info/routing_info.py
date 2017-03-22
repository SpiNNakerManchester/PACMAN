# pacman imports
from pacman import exceptions


class RoutingInfo(object):
    """ An association of a set of edges to a non-overlapping set of keys\
        and masks
    """

    __slots__ = [
        # Partition information indexed by partition
        "_partition_info_by_partition",

        # Partition information indexed by edge pre vertex and partition id
        # name
        "_partition_info_by_pre_vertex",

        # Partition information by edge
        "_partition_info_by_edge"
    ]

    def __init__(self, partition_info_items=None):
        """

        :param partition_info_items: The partition information items to add
        :type partition_info_items: iterable of\
                    :py:class:`pacman.model.routing_info.partition_routing_info.PartitionRoutingInfo`
                    or none
        :raise pacman.exceptions.PacmanAlreadyExistsException: If there are \
                    two partition information objects with the same partition
        """

        # Partition information indexed by partition
        self._partition_info_by_partition = dict()

        # Partition information indexed by edge pre vertex and partition id
        # name
        self._partition_info_by_pre_vertex = dict()

        # Partition information by edge
        self._partition_info_by_edge = dict()

        if partition_info_items is not None:
            for partition_info_item in partition_info_items:
                self.add_partition_info(partition_info_item)

    def add_partition_info(self, partition_info):
        """ Add a partition information item

        :param partition_info: The partition information item to add
        :type partition_info:\
            :py:class:`pacman.model.routing_info.partition_routing_info.PartitionRoutingInfo`
        :rtype: None
        :raise pacman.exceptions.PacmanAlreadyExistsException:\
            If the partition is already in the set of edges
        """
        partition = partition_info.partition

        if partition in self._partition_info_by_partition:
            raise exceptions.PacmanAlreadyExistsException(
                "Partition", str(partition_info))

        if ((partition.pre_vertex, partition.identifier)
                in self._partition_info_by_pre_vertex):
            raise exceptions.PacmanAlreadyExistsException(
                "Partition", str(partition_info))

        self._partition_info_by_partition[partition] = partition_info
        self._partition_info_by_pre_vertex[
            partition.pre_vertex, partition.identifier] = partition_info

        for edge in partition.edges:
            self._partition_info_by_edge[edge] = partition_info

    def get_first_key_from_partition(self, partition):
        """ Get the first key associated with a particular partition

        :param partition: The partition to get the first key of
        :type partition:\
                :py:class:`pacman.model.graph.simple_outgoing_edge_partition.OutgoingEdgePartition`
        :return: The routing key or None if the partition does not exist
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        if partition in self._partition_info_by_partition:
            return self._partition_info_by_partition[
                partition].keys_and_masks[0].key
        return None

    def get_routing_info_from_partition(self, partition):
        """

        :param partition: The partition to set the number of keys for
        :type partition:\
                    :py:class:`pacman.model.graph.simple_outgoing_edge_partition.OutgoingEdgePartition`
        :return: the partition_routing_info for the partition
        """
        if partition in self._partition_info_by_partition:
            return self._partition_info_by_partition[partition]
        return None

    def get_routing_info_from_pre_vertex(self, vertex, partition_id):
        """ Get routing information for edges with a given partition_id from\
            a pre vertex

        :param vertex: The pre_vertex to search for
        :param partition_id: The id of the partition for which to get\
                    the routing information
        """
        if (vertex, partition_id) in self._partition_info_by_pre_vertex:
            return self._partition_info_by_pre_vertex[vertex, partition_id]
        return None

    def get_first_key_from_pre_vertex(self, vertex, partition_id):
        """ Get the first key for the partition starting at a vertex

        :param vertex: The vertex which the partition starts at
        :param partition_id: The id of the partition for which to get\
                    the routing information
        :return: The routing key of the partition
        :rtype: int
        """
        if (vertex, partition_id) in self._partition_info_by_pre_vertex:
            return self._partition_info_by_pre_vertex[
                vertex, partition_id].keys_and_masks[0].key
        return None

    def get_routing_info_for_edge(self, edge):
        """ Get routing information for an edge

        :param edge: The edge to search for
        """
        return self._partition_info_by_edge.get(edge, None)

    def get_first_key_for_edge(self, edge):
        """ Get routing key for an edge

        :param edge: The edge to search for
        """
        if edge in self._partition_info_by_edge:
            return self._partition_info_by_edge[edge].keys_and_masks[0].key
        return None

    def __iter__(self):
        """ returns a iterator for the partition routing information

        :return: a iterator of partition routing information
        """
        return iter(self._partition_infos_by_key)
