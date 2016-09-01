
class Placement(object):
    """ The placement of a vertex on to a machine chip and core
    """

    __slots__ = [

        # the machine vertex that is placed on the core represented
        "_vertex",

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

    def __init__(self, vertex, x, y, p):
        """

        :param vertex: The vertex that has been placed
        :type vertex:\
            :py:class:`pacman.model.graph.machine.abstract_machine_vertex.AbstractMachineVertex`
        :param x: the x-coordinate of the chip on which the vertex is placed
        :type x: int
        :param y: the y-coordinate of the chip on which the vertex is placed
        :type y: int
        :param p: the id of the processor on which the vertex is placed
        :type p: int
        """
        self._vertex = vertex
        self._x = x
        self._y = y
        self._p = p

    @property
    def vertex(self):
        """ The vertex that was placed

        :return: a vertex
        :rtype:\
            :py:class:`pacman.model.graph.machine.abstract_machine_vertex.AbstractMachineVertex`
        :raise None: does not raise any known exceptions
        """
        return self._vertex

    @property
    def x(self):
        """ The x-coordinate of the chip where the vertex is placed

        :return: The x-coordinate
        :rtype: int
        """
        return self._x

    @property
    def y(self):
        """ The y-coordinate of the chip where the vertex is placed

        :return: The y-coordinate
        :rtype: int
        """
        return self._y

    @property
    def p(self):
        """ The id of the processor of the chip where the vertex is placed

        :return: The processor id
        :rtype: int
        """
        return self._p

    def __eq__(self, other):
        if not isinstance(other, Placement):
            return False
        return (self._x == other.x and self._y == other.y and
                self._p == other.p and self._vertex == other.vertex)

    def __hash__(self):
        return hash((self._x, self._y, self._p, self._vertex))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "Placement(vertex={}, x={}, y={}, p={})".format(
            self._vertex, self._x, self._y, self._p)
