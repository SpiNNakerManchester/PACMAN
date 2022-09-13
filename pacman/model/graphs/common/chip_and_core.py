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

class ChipAndCore(object):
    """ A constraint to place a vertex on a specific chip and, optionally, a\
        specific core on that chip.
    """

    __slots__ = [
        # the chip x coord in the SpiNNaker machine to which the machine
        # vertex is placed
        "_x",

        # the chip y coord in the SpiNNaker machine to which the machine
        # vertex is placed
        "_y",

        # The processor ID on chip (x,y) that this vertex is placed on within
        # the SpiNNaker machine; may be None
        "_p",
    ]

    def __init__(self, x, y, p=None):
        """
        :param int x: the x-coordinate of the chip
        :param int y: the y-coordinate of the chip
        :param p: the processor (if any) of the chip
        :type p: int or None
        """
        self._x = int(x)
        self._y = int(y)
        self._p = None if p is None else int(p)

    @property
    def x(self):
        """ The x-coordinate of the chip

        :rtype: int
        """
        return self._x

    @property
    def y(self):
        """ The y-coordinate of the chip

        :rtype: int
        """
        return self._y

    @property
    def p(self):
        """ The processor on the chip, or None if that is not constrained

        :rtype: int or None
        """
        return self._p

    def __repr__(self):
        if self._p is None:
            return f"X:{self._x},Y{self._y}"
        else:
            return f"X:{self._x},Y:{self._y},P:{self._p}"

    def __eq__(self, other):
        if not isinstance(other, ChipAndCore):
            return False
        return (self._x, self._y, self._p) == (other.x, other.y, other.p)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self._x, self._y, self._p))
