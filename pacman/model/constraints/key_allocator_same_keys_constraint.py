from pacman.model.constraints.abstract_key_allocator_constraint \
    import AbstractKeyAllocatorConstraint


class KeyAllocatorSameKeysConstraint(AbstractKeyAllocatorConstraint):
    """ A constraint that says that the keys allocated to a given partitioned\
        edge should be the same as the keys allocated to another partitioned\
        edge
    """

    def __init__(self, partitioned_edge_to_match):
        """
        :param partitioned_edge_to_match: The partitioned edge to match
        :type partitioned_edge_to_match:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
        """
        AbstractKeyAllocatorConstraint.__init__(
            self, "Key allocator constraint where the keys for this"
                  " partitioned edge should match those for {}".format(
                      partitioned_edge_to_match))

        self._partitioned_edge_to_match = partitioned_edge_to_match

    def is_key_allocator_constraint(self):
        return True

    @property
    def partitioned_edge_to_match(self):
        """ The partitioned edge to be matched

        :return: A partitioned edge
        :rtype:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
        """
        return self._partitioned_edge_to_match
