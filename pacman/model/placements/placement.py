"""
Placement file
"""


class Placement(object):
    """ Represents a placement of a subvertex on a specific processor on a\
        specific chip in the machine
    """

    def __init__(self, subvertex, x, y, p):
        """

        :param subvertex: The subvertex that has been placed
        :type subvertex: None or
        :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :param x: the x-coordinate of the chip on which the subvertex is placed
        :type x: int
        :param y: the y-coordinate of the chip on which the subvertex is placed
        :type y: int
        :param p: the id of the processor on which the subvertex is placed
        :type p: int or None
        :raise None: does not raise any known exceptions
        """
        self._subvertex = subvertex
        self._x = x
        self._y = y
        self._p = p

    @property
    def subvertex(self):
        """ The subvertex that was placed

        :return: a subvertex
        :rtype:
        :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :raise None: does not raise any known exceptions
        """
        return self._subvertex

    @property
    def x(self):
        """ The x-coordinate of the chip where the subvertex is placed

        :return: The x-coordinate
        :rtype: int
        """
        return self._x

    @property
    def y(self):
        """ The y-coordinate of the chip where the subvertex is placed

        :return: The y-coordinate
        :rtype: int
        """
        return self._y

    @property
    def p(self):
        """ The id of the processor of the chip where the subvertex is placed

        :return: The processor id
        :rtype: int
        """
        return self._p

    def __eq__(self, other):
        if not isinstance(other, Placement):
            return False
        return (self._x == other.x and self._y == other.y and
                self._p == other.p and self._subvertex == other.subvertex)

    def __hash__(self):
        if self._subvertex is None and self._p is None:
            return hash((self._x, self._y))
        elif self._subvertex is None and self._p is not None:
            return hash((self._x, self._y, self._p))
        elif self._subvertex is not None and self._p is None:
            return hash((self._x, self._y, self._subvertex))
        else:
            return hash((self._x, self._y, self._p, self._subvertex))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        """ generates a human readable description of the placement object

        :return: string representation of the placement object
        """
        return "placement object for core {}:{}:{}".format(self._x, self._y,
                                                           self._p)
