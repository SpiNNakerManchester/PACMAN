from pacman.model.routing_info.abstract_machine_partition_n_keys_map \
    import AbstractMachinePartitionNKeysMap


class DictBasedMachinePartitionNKeysMap(AbstractMachinePartitionNKeysMap):
    """ A python dict-based implementation of the\
        AbstractMachinePartitionNKeysMap
    """

    def __init__(self):
        self._n_keys_map = dict()

    def set_n_keys_for_partition(self, partition, n_keys):
        """ Set the number of keys required by a machine outgoing edge\
            partition

        :param partition: The partition to set the number of keys for
        :type partition:\
            :py:class:`pacman.model.graph.simple_outgoing_edge_partition.OutgoingEdgePartition`
        :param n_keys: The number of keys required by the edge
        :type n_keys: int
        """
        self._n_keys_map[partition] = n_keys

    def n_keys_for_partition(self, partition):
        """

        :param partition: The partition to set the number of keys for
        :type partition:\
            :py:class:`pacman.model.graph.simple_outgoing_edge_partition.OutgoingEdgePartition`
        :return:
        """
        return self._n_keys_map[partition]
