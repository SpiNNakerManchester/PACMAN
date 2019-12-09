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

import collections
from pacman.exceptions import PacmanValueError


class Slice(collections.namedtuple('Slice', 'lo_atom hi_atom n_atoms')):
    """ Represents a slice of a vertex.

    :attr int lo_atom: The lowest atom represented in the slice.
    :attr int hi_atom: The highest atom represented in the slice.
    :attr int n_atoms: The number of atoms represented by the slice.
    :attr slice as_slice: This slice represented as a `slice` object (for
        use in indexing lists, arrays, etc.)
    """
    def __new__(cls, lo_atom, hi_atom):
        """ Create a new Slice object.

        :param int lo_atom: Index of the lowest atom to represent.
        :param int hi_atom: Index of the highest atom to represent.
        :raises PacmanValueError: If the bounds of the slice are invalid.
        """
        if lo_atom < 0:
            raise PacmanValueError('lo_atom < 0')
        if hi_atom < lo_atom:
            raise PacmanValueError(
                'hi_atom {:d} < lo_atom {:d}'.format(hi_atom, lo_atom))

        # Number of atoms represented by this slice
        n_atoms = hi_atom - lo_atom + 1

        # Create the Slice object as a `namedtuple` with these pre-computed
        # values filled in.
        return super(cls, Slice).__new__(cls, lo_atom, hi_atom, n_atoms)

    @property
    def as_slice(self):
        # Slice for accessing arrays of values
        return slice(self.lo_atom, self.hi_atom + 1)
