# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


class Placement(object):
    """ The placement of a vertex on to a machine chip and core.
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

        # The processor ID on chip (x,y) that this vertex is placed on within
        # the SpiNNaker machine
        "_p",
    ]

    def __init__(self, vertex, x, y, p):
        """
        :param MachineVertex vertex: The vertex that has been placed
        :param int x:
            the x-coordinate of the chip on which the vertex is placed
        :param int y:
            the y-coordinate of the chip on which the vertex is placed
        :param int p: the ID of the processor on which the vertex is placed
        """
        self._vertex = vertex
        self._x = x
        self._y = y
        self._p = p

    @property
    def vertex(self):
        """ The vertex that was placed.

        :rtype: MachineVertex
        """
        return self._vertex

    @property
    def x(self):
        """ The x-coordinate of the chip where the vertex is placed.

        :rtype: int
        """
        return self._x

    @property
    def y(self):
        """ The y-coordinate of the chip where the vertex is placed.

        :rtype: int
        """
        return self._y

    @property
    def p(self):
        """ The ID of the processor of the chip where the vertex is placed.

        :rtype: int
        """
        return self._p

    @property
    def location(self):
        """ The (x,y,p) tuple that represents the location of this placement.

        :rtype: tuple(int,int,int)
        """
        return (self._x, self._y, self._p)

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
