from pacman.model.constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint
import sys


class PlacerStartPlacementAtCoreConstraint(AbstractPlacerConstraint):
    """ Creates a constraint object to place a vertex or a subvertex on a\
        specific chip, and optionally a specific core on that chip
    """

    def __init__(self, x, y, p):
        """

        :param x: the x-coordinate of the chip
        :type x: int
        :param y: the y-coordinate of the chip
        :type y: int
        :param p: the processor of the chip to start placing partitioned_vertices
        :type p: int
        :raise None: does not raise any known exceptions
        """
        AbstractPlacerConstraint.__init__(
            self, label="placer start placement at chip and core constraint at "
                        "coords {},{},{}".format(x, y, p))
        self._x = x
        self._y = y
        self._p = p

    def is_placer_constraint(self):
        return True

    @property
    def rank(self):
        if self.p is not None:
            return sys.maxint
        else:
            return sys.maxint - 1

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
