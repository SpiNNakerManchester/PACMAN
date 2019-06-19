from spinn_utilities.overrides import overrides
from .abstract_machine_partition_n_keys_map import (
    AbstractMachinePartitionNKeysMap)


class DictBasedMachinePartitionNKeysMap(AbstractMachinePartitionNKeysMap):
    """ A python dict-based implementation of the\
        :py:class:`pacman.model.routing_info.AbstractMachinePartitionNKeysMap`
    """

    __slots__ = [
        # A mapping of [partition] -> number of keys to use via this partition
        "_n_keys_map"
    ]

    def __init__(self):
        self._n_keys_map = dict()

    def set_n_keys_for_partition(self, partition, n_keys):
        """ Set the number of keys required by a machine outgoing edge\
            partition

        :param partition: The partition to set the number of keys for
        :type partition:\
            :py:class:`pacman.model.graphs.impl.OutgoingEdgePartition`
        :param n_keys: The number of keys required by the edge
        :type n_keys: int
        """
        self._n_keys_map[partition] = int(n_keys)

    @overrides(AbstractMachinePartitionNKeysMap.n_keys_for_partition)
    def n_keys_for_partition(self, partition):
        if partition in self._n_keys_map:
            return self._n_keys_map[partition]

