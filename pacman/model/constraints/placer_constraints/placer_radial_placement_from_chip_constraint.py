import sys

from pacman.model.constraints.abstract_constraints.\
    abstract_placer_constraint import AbstractPlacerConstraint


class PlacerRadialPlacementFromChipConstraint(AbstractPlacerConstraint):
    """ Creates a constraint object to place a vertex or a subvertex on a\
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
        AbstractPlacerConstraint.__init__(
            self, label="placer radial placement from chip and core "
                        "constraint at coords {},{}".format(x, y))

        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def rank(self):
        return sys.maxint - 5

    def is_placer_constraint(self):
        return True
