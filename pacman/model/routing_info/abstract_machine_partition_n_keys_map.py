from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractMachinePartitionNKeysMap(object):
    """ A map that provides the number of keys required by each partition
    """

    @abstractmethod
    def n_keys_for_partition(self, partition):
        """ The number of keys required by the given partition

        :param partition: The partition to set the number of keys for
        :type partition:\
                    :py:class:`pacman.model.graph.simple_outgoing_edge_partition.OutgoingEdgePartition`
        :return: The number of keys required by the partition
        :rtype: int
        """
        pass
