# pacman imports
from pacman import exceptions
from pacman.model.partitionable_graph.abstract_partitionable_edge \
    import AbstractPartitionableEdge
from pacman.model.partitioned_graph.abstract_partitioned_edge \
    import AbstractPartitionedEdge


class RoutingInfo(object):
    """ An association of a set of subedges to a non-overlapping set of keys\
        and masks
    """

    def __init__(self, partition_info_items=None):
        """

        :param partition_info_items: The subedge information items to add
        :type partition_info_items: iterable of\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.PartitionRoutingInfo`
                    or none
        :raise pacman.exceptions.PacmanAlreadyExistsException: If there are \
                    two subedge information objects with the same edge
        """

        # Partition information indexed by partition
        self._partition_info_by_partition = dict()

        # Partition information indexed by edge pre vertex and partition id
        # name
        self._partition_info_by_pre_vertex = dict()

        # Partition informations indexed by edge post vertex and partition id
        self._partition_infos_by_post_vertex = dict()

        if partition_info_items is not None:
            for partition_info_item in partition_info_items:
                self.add_partition_info(partition_info_item)

    def add_partition_info(self, partition_info):
        """ Add a subedge information item

        :param partition_info: The subedge information item to add
        :type partition_info:\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.PartitionRoutingInfo`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanAlreadyExistsException: If the subedge\
                    is already in the set of subedges
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
            post_vertex = None
            if isinstance(edge, AbstractPartitionableEdge):
                post_vertex = edge.post_vertex
            elif isinstance(edge, AbstractPartitionedEdge):
                post_vertex = edge.post_subvertex

            if ((post_vertex, partition.identifier)
                    not in self._partition_infos_by_post_vertex):
                self._partition_infos_by_post_vertex[
                    post_vertex, partition.identifier] = list()

            self._partition_infos_by_post_vertex[
                post_vertex, partition.identifier].append(partition_info)

    @property
    def all_partition_info(self):
        """ The subedge information for all subedges

        :return: iterable of subedge information
        :rtype: iterable of\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.PartitionRoutingInfo`
        :raise None: does not raise any known exceptions
        """
        return self._partition_info_by_partition.itervalues()

    def get_keys_and_masks_from_partition(self, partition):
        """ Get the key associated with a particular partition

        :param partition: The partition to set the number of keys for
        :type partition:\
                    :py:class:`pacman.model.graph.outgoing_edge_partition.OutgoingEdgePartition`
        :return: The routing key or None if the subedge does not exist
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        if partition in self._partition_info_by_partition:
            return self._partition_info_by_partition[partition].keys_and_masks
        return None

    def get_routing_info_from_partition(self, partition):
        """
        :param partition: The partition to set the number of keys for
        :type partition:\
                    :py:class:`pacman.model.graph.outgoing_edge_partition.OutgoingEdgePartition`
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

    def get_routing_infos_to_post_vertex(self, vertex, partition_id):
        """ Get a list of routing information for edges with a given\
            partition_id to a post vertex

        :param vertex: The post_vertex to search for
        :param partition_id: The id of the partition for which to get\
                    the routing information
        """
        if (vertex, partition_id) in self._partition_infos_by_post_vertex:
            return self._partition_infos_by_post_vertex[vertex, partition_id]
        return None

    def __iter__(self):
        """ returns a iterator for the partition routing information

        :return: a iterator of partition routing information
        """
        return iter(self._partition_infos_by_key)
