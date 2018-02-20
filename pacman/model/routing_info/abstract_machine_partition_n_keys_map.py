from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractMachinePartitionNKeysMap(object):
    """ A map that provides the number of keys required by each partition
    """

    __slots__ = []

    @abstractmethod
    def n_keys_for_partition(self, partition):
        """ The number of keys required by the given partition

        :param partition: The partition to set the number of keys for
        :type partition:\
            :py:class:`pacman.model.graphs.impl.OutgoingEdgePartition`
        :return: The number of keys required by the partition
        :rtype: int
        """
