from .abstract_placer_constraint import AbstractPlacerConstraint


class SameChipAsConstraint(AbstractPlacerConstraint):
    """ Indicates that a vertex should be placed on the same chip as another
        vertex
    """

    __slots__ = [
        #  The vertex to place on the same chip
        "_vertex"
    ]

    def __init__(self, vertex):
        """

        :param vertex: The vertex to place on the same chip
        """
        self._vertex = vertex

    @property
    def vertex(self):
        """ The vertex to place on the same chip
        """
        return self._vertex

    def __repr__(self):
        return "SameChipAsConstraint(vertex={})".format(self._vertex)

    def __eq__(self, other):
        if not isinstance(other, SameChipAsConstraint):
            return False
        return self._vertex == other.vertex  

    def __hash__(self):
        return hash((self._vertex, ))
