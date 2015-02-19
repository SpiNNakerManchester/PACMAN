from pacman.model.routing_info.abstract_partitioned_edge_n_keys_map \
    import AbstractPartitionedEdgeNKeysMap


class DictBasedPartitionedEdgeNKeysMap(AbstractPartitionedEdgeNKeysMap):
    """ A python dict-based implementation of the\
        AbstractPartitionedEdgeNKeysMap
    """

    def __init__(self):
        self._n_keys_map = dict()

    def set_n_keys_for_patitioned_edge(self, partitioned_edge, n_keys):
        """ Sets the number of keys required by a partitioned edge

        :param partitioned_edge: The partitioned edge to set the number of\
                    keys for
        :type partitioned_edge:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
        :param n_keys: The number of keys required by the edge
        :type n_keys: int
        """
        self._n_keys_map[partitioned_edge] = n_keys

    def n_keys_for_partitioned_edge(self, partitioned_edge):
        return self._n_keys_map[partitioned_edge]
