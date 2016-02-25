from pacman.model.abstract_classes.abstract_partitioned_edge_n_keys_map \
    import AbstractPartitionedPartitionNKeysMap


class DictBasedPartitionedPartitionNKeysMap(AbstractPartitionedPartitionNKeysMap):
    """ A python dict-based implementation of the\
        AbstractPartitionedEdgeNKeysMap
    """

    def __init__(self):
        self._n_keys_map = dict()

    def set_n_keys_for_partition(self, partition, n_keys):
        """ Sets the number of keys required by a partitioned edge

        :param partition: The partition to set the number of keys for
        :type partition:\
                    :py:class:`pacman.utilities.utility_objs.outgoing_edge_partition.OutgoingEdgePartition`
        :param n_keys: The number of keys required by the edge
        :type n_keys: int
        """
        self._n_keys_map[partition] = n_keys

    def n_keys_for_partition(self, partition):
        """

        :param partition: The partition to set the number of keys for
        :type partition:\
                    :py:class:`pacman.utilities.utility_objs.outgoing_edge_partition.OutgoingEdgePartition`
        :return:
        """
        return self._n_keys_map[partition]
