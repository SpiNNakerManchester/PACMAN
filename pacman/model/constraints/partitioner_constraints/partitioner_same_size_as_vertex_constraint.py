# pacman imports
from pacman.model.constraints.partitioner_constraints\
    .abstract_partitioner_constraint import AbstractPartitionerConstraint


class PartitionerSameSizeAsVertexConstraint(AbstractPartitionerConstraint):
    """ A constraint which indicates that a vertex must be split in the\
        same way as another vertex
    """

    def __init__(self, vertex):
        """

        :param vertex: The vertex to which the constraint refers
        :type vertex: \
            :py:class:`pacman.model.graph.application.abstract_application_vertex.AbstractApplicationVertex`
        :raise None: does not raise any known exceptions
        """
        self._vertex = vertex

    @property
    def vertex(self):
        """ The vertex to partition with

        :return: the vertex
        :rtype:\
                    :py:class:`pacman.model.graph.application.abstract_application_vertex.AbstractApplicationVertex`
        :raise None: does not raise any known exceptions
        """
        return self._vertex
