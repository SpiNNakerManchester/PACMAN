from pacman.model.constraints.abstract_constraint import AbstractConstraint


class VertexHasDependentConstraint(AbstractConstraint):
    """ A constraint which indicates that a vertex A must have a edge to another
    vertex B, where B only exists becuase A uses it.
    """

    def __init__(self, vertex):
        """

        :param vertex: The vertex to which the constraint refers
        :type vertex: :py:class:`pacman.model.graph.vertex.Vertex`
        :raise None: does not raise any known exceptions
        """
        AbstractConstraint.__init__(
            self, "partitioner same size as other vertex constraint with vertex"
                  "{}".format(vertex))
        self._vertex = vertex

    @property
    def vertex(self):
        """ The vertex to link with

        :return: the vertex
        :rtype: :py:class:`pacman.model.graph.vertex.Vertex`
        :raise None: does not raise any known exceptions
        """
        return self._vertex
