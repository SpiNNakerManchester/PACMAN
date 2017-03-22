from pacman.model.constraints.placer_constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint


class PlacerSameChipAsConstraint(AbstractPlacerConstraint):
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
        return "PlacerSameChipAsConstraint(vertex={})".format(self._vertex)
