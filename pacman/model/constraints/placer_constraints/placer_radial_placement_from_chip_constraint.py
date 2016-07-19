from pacman.model.constraints.placer_constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint


class PlacerRadialPlacementFromChipConstraint(AbstractPlacerConstraint):
    """ Creates a constraint object to place the subvertices of a vertex on a\
        specific chip, and optionally a specific core on that chip
    """

    def __init__(self, x, y):
        """

        :param x: the x-coordinate of the chip
        :type x: int
        :param y: the y-coordinate of the chip
        :type y: int
        :raise None: does not raise any known exceptions
        """
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y
