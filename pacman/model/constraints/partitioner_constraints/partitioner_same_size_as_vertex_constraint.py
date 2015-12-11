# pacman imports
from pacman.model.constraints.abstract_constraints\
    .abstract_partitioner_constraint import AbstractPartitionerConstraint


class PartitionerSameSizeAsVertexConstraint(AbstractPartitionerConstraint):
    """ A constraint which indicates that a vertex must be partitioned so that\
        there are the same number of subvertices and the same number of atoms\
        in each subvertex as those created for another vertex
    """

    def __init__(self, vertex):
        """

        :param vertex: The vertex to which the constraint refers
        :type vertex: \
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :raise None: does not raise any known exceptions
        """
        AbstractPartitionerConstraint.__init__(
            self, "partitioner same size as other vertex constraint with"
                  " vertex {}".format(vertex.label))
        self._vertex = vertex

    def is_partitioner_constraint(self):
        """
        helper method for is instance
        :return:
        """
        return True

    @property
    def vertex(self):
        """ The vertex to partition with

        :return: the vertex
        :rtype:\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :raise None: does not raise any known exceptions
        """
        return self._vertex
