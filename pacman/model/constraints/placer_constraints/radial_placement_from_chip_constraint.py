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

from .abstract_placer_constraint import AbstractPlacerConstraint


class RadialPlacementFromChipConstraint(AbstractPlacerConstraint):
    """ A constraint that attempts to place a vertex as close to a chip\
        as possible (including on it).
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
        :param int x: the x-coordinate of the chip
        :param int y: the y-coordinate of the chip
        """
        self._x = int(x)
        self._y = int(y)

    @property
    def x(self):
        """ The chip x-coordinate in the SpiNNaker machine to which the \
            machine vertex is placed.

        :rtype: int
        """
        return self._x

    @property
    def y(self):
        """ The chip y-coordinate in the SpiNNaker machine to which the \
            machine vertex is placed.

        :rtype: int
        """
        return self._y

    def __repr__(self):
        return "RadialPlacementFromChipConstraint(x={}, y={})".format(
            self._x, self._y)

    def __eq__(self, other):
        if not isinstance(other, RadialPlacementFromChipConstraint):
            return False
        return (self._x, self._y) == (other.x, other.y)

    def __ne__(self, other):
        if not isinstance(other, RadialPlacementFromChipConstraint):
            return True
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self._x, self._y))
