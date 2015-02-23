from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractPartitionedEdgeNKeysMap(object):
    """ A map that provides the number of keys required by each partitioned\
        edge
    """

    @abstractmethod
    def n_keys_for_partitioned_edge(self, partitioned_edge):
        """ The number of keys required by the given partitioned edge

        :param partitioned_edge: A paritioned edge
        :type partitioned_edge:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
        :return: The number of keys required by the partitioned edge
        :rtype: int
        """
        pass
