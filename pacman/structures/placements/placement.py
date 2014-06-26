__author__ = 'daviess'


class Placement(object):
    """
    Creates a new placement for a particular subvertex on a specific processor
    """

    def __init__(self, subvertex, x, y, p):
        """

        :param subvertex: subvertex to be placed
        :param x: the x coordinate of the chip on which the subvertex is placed
        :param y: the y coordinate of the chip on which the subvertex is placed
        :param p: the processor on which the subvertex is placed
        :type subvertex: pacman.subgraph.subvertex.Subvertex
        :type x: int
        :type y: int
        :type p: int
        :return: a new placement object
        :rtype: pacman.placements.placement.Placement
        :raise None: does not raise any known exceptions
        """
        self._subvertex = subvertex
        self._x = x
        self._y = y
        self._p = p

    @property
    def subvertex(self):
        """
        Returns the subvertex of this placement object

        :return: the subvertex of this placement object
        :rtype: pacman.subgraph.subvertex.Subvertex
        :raise None: does not raise any known exceptions
        """
        return self._subvertex

    @property
    def coordinates(self):
        """
        Returns the coordinates of the chip and processor on which the\
        subvertex has been placed

        :return: the coordinates of this placement object
        :rtype: {"x": int, "y": int, "p": int}
        :raise None: does not raise any known exceptions
        """
        return {"x": self._x, "y": self._y, "p": self._p}

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return to_string(self._x, self._y, self._p)

    @staticmethod
    def to_string(x, y, p):
        return "{}:{}:{}".format(x, y, p)