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


class BoardConstraint(AbstractPlacerConstraint):
    """ A constraint on the board on which a placement is made.
    """

    __slots__ = [
        #  The IP address of the Ethernet of the board to be used
        "_board_address"
    ]

    def __init__(self, board_address):
        """
        :param str board_address:
            The IP address of the Ethernet of the board to be used
        """
        self._board_address = board_address

    @property
    def board_address(self):
        """ The board of the constraint

        :rtype: str
        """
        return self._board_address

    def __repr__(self):
        return "BoardConstraint(board_address=\"{}\")".format(
            self._board_address)

    def __eq__(self, other):
        if not isinstance(other, BoardConstraint):
            return False
        return self._board_address == other.board_address

    def __ne__(self, other):
        if not isinstance(other, BoardConstraint):
            return True
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self._board_address,))
