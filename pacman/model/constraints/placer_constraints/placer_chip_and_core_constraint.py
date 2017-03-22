from pacman.model.constraints.placer_constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint


class PlacerChipAndCoreConstraint(AbstractPlacerConstraint):
    """ A constraint to place a vertex on a specific chip and, optionally, a\
        specific core on that chip
    """

    __slots__ = [
        # the chip x coord in the SpiNNaker machine to which the machine
        # vertex is placed
        "_x",

        # the chip y coord in the SpiNNaker machine to which the machine
        # vertex is placed
        "_y",

        # The processor id on chip (x,y) that this vertex is placed on within
        # the SpiNNaker machine
        "_p",
    ]

    def __init__(self, x, y, p=None):
        """

        :param x: the x-coordinate of the chip
        :type x: int
        :param y: the y-coordinate of the chip
        :type y: int
        :param p: the processor (if any) of the chip
        :type p: int
        :raise None: does not raise any known exceptions
        """
        self._x = x
        self._y = y
        self._p = p

    @property
    def x(self):
        """ The x-coordinate of the chip

        :return: the x-coordinate
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._x

    @property
    def y(self):
        """ The y-coordinate of the chip

        :return: the y-coordinate
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._y

    @property
    def p(self):
        """ The processor on the chip

        :return: the processor id or None
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._p

    @property
    def location(self):
        """ The location as a dictionary with three keys: "x", "y" and "p"

        :return: a dictionary containing the location
        :rtype: dict of {"x": int, "y": int, "p": int}
        :raise None: does not raise any known exceptions
        """
        return {"x": self._x, "y": self._y, "p": self._p}

    def __repr__(self):
        return "PlacerChipAndCoreConstraint(x={}, y={}, p={})".format(
            self._x, self._y, self._p)
