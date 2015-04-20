from pacman.model.abstract_classes.abstract_partitionable_edge import \
    AbstractPartitionableEdge
from pacman.model.partitioned_graph.multi_cast_partitioned_edge import \
    MultiCastPartitionedEdge


class TestPartitionableEdge(AbstractPartitionableEdge):
    """
    test class for creating edges
    """

    def __init__(self, pre_vertex, post_vertex, label=None, constraints=None):
        AbstractPartitionableEdge.__init__(
            self, pre_vertex, post_vertex, label, constraints)

    def create_subedge(self, pre_subvertex, post_subvertex, constraints=None,
                       label=None):
        """ method to create subedges

        :param pre_subvertex:
        :param post_subvertex:
        :param constraints:
        :param label:
        :return:
        """
        if constraints is not None:
            if self._constraints is not None:
                constraints.extend(self._constraints)
        else:
            constraints = self._constraints
            print constraints
        return MultiCastPartitionedEdge(pre_subvertex, post_subvertex,
                                        label, constraints)

    def is_partitionable_edge(self):
        """ helper for isinstance

        :return:
        """
        return True