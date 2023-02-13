# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


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
        """ The vertex that was placed

        :rtype: MachineVertex
        """
        return self._vertex

    @property
    def x(self):
        """ The x-coordinate of the chip where the vertex is placed

        :rtype: int
        """
        return self._x

    @property
    def y(self):
        """ The y-coordinate of the chip where the vertex is placed

        :rtype: int
        """
        return self._y

    @property
    def p(self):
        """ The ID of the processor of the chip where the vertex is placed

        :rtype: int
        """
        return self._p

    @property
    def location(self):
        """ The (x,y,p) tuple that represents the location of this placement.

        :rtype: tuple(int,int,int)
        """
        return (self._x, self._y, self._p)

    @property
    def xy(self):
        """ The (x,y) tuple that represents the chip of this placement.

        :rtype: tuple(int,int)
        """
        return (self._x, self._y)

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
