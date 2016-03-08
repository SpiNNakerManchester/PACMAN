from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractPartitionedEdgeNKeysMap(object):
    """ A map that provides the number of keys required by each partitioned\
        edge
    """

    @abstractmethod
    def n_keys_for_partition(self, partition):
        """ The number of keys required by the given partitioned edge

        :param partition: The partition to set the number of keys for
        :type partition:\
                    :py:class:`pacman.utilities.utility_objs.outgoing_edge_partition.OutgoingEdgePartition`
        :return: The number of keys required by the partitioned edge
        :rtype: int
        """
        pass
