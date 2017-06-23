# pacman imports
from .abstract_partitioner_constraint import AbstractPartitionerConstraint


class PartitionerSameSizeAsVertexConstraint(AbstractPartitionerConstraint):
    """ A constraint which indicates that a vertex must be split in the\
        same way as another vertex
    """

    __slots__ = [
        # The application vertex to which the constraint refers
        "_vertex"
    ]

    def __init__(self, vertex):
        """

        :param vertex: The vertex to which the constraint refers
        :type vertex: \
            :py:class:`pacman.model.graph.application.application_vertex.ApplicationVertex`
        :raise None: does not raise any known exceptions
        """
        self._vertex = vertex

    @property
    def vertex(self):
        """ The vertex to partition with

        :return: the vertex
        :rtype:\
                    :py:class:`pacman.model.graph.application.application_vertex.ApplicationVertex`
        :raise None: does not raise any known exceptions
        """
        return self._vertex

    def __repr__(self):
        return "PartitionerSameSizeAsVertexConstraint(vertex={})".format(
            self._vertex)
