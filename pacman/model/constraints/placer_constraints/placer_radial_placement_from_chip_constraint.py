from pacman.model.constraints.placer_constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint
from pacman.model.decorators.overrides import overrides


class PlacerRadialPlacementFromChipConstraint(AbstractPlacerConstraint):
    """ A constraint that attempts to place a vertex as close to a chip\
        as possible (including on it)
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

    @overrides(AbstractPlacerConstraint.label)
    def label(self):
        return "placer radial placement from chip and core constraint at " \
               "coords {},{}".format(self.x, self.y)