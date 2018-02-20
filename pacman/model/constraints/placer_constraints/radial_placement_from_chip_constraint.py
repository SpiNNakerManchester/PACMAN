from .abstract_placer_constraint import AbstractPlacerConstraint


class RadialPlacementFromChipConstraint(AbstractPlacerConstraint):
    """ A constraint that attempts to place a vertex as close to a chip\
        as possible (including on it)
    """

    __slots__ = [
        # the chip x coord in the SpiNNaker machine to which the machine
        # vertex is placed
        "_x",

        # the chip y coord in the SpiNNaker machine to which the machine
        # vertex is placed
        "_y"
    ]

    def __init__(self, x, y):
        """

        :param x: the x-coordinate of the chip
        :type x: int
        :param y: the y-coordinate of the chip
        :type y: int
        :raise None: does not raise any known exceptions
        """
        self._x = int(x)
        self._y = int(y)

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def __repr__(self):
        return "RadialPlacementFromChipConstraint(x={}, y={})".format(
            self._x, self._y)

    def __eq__(self, other):
        if not isinstance(other, RadialPlacementFromChipConstraint):
            return False
        return (self._x, self._y) == (other.x, other.y)  

    def __hash__(self):
        return hash((self._x, self._y))
