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


class Slice(collections.namedtuple('Slice',
                                   'lo_atom hi_atom n_atoms shape start')):
    """ Represents a slice of a vertex.

    :attr int lo_atom: The lowest atom represented in the slice.
    :attr int hi_atom: The highest atom represented in the slice.
    :attr int n_atoms: The number of atoms represented by the slice.
    :attr slice as_slice: This slice represented as a `slice` object (for
        use in indexing lists, arrays, etc.)
    :attr tuple(int,...) shape: The shape of the atoms over multiple
        dimensions.  By default the shape will be 1-dimensional.
    :attr tuple(int,...) start: The start coordinates of the slice.  By default
        this will be lo_atom in 1 dimension.
    """
    def __new__(cls, lo_atom, hi_atom, shape=None, start=None):
        """ Create a new Slice object.

        :param int lo_atom: Index of the lowest atom to represent.
        :param int hi_atom: Index of the highest atom to represent.
        :raises PacmanValueError: If the bounds of the slice are invalid.
        """
        if not isinstance(lo_atom, int):
            raise Exception("lo atom needs to be a int")
        if not isinstance(hi_atom, int):
            raise Exception("hi atom needs to be a int")

        if lo_atom < 0:
            raise PacmanValueError('lo_atom < 0')
        if hi_atom < lo_atom:
            raise PacmanValueError(
                'hi_atom {:d} < lo_atom {:d}'.format(hi_atom, lo_atom))

        if (start is None) != (shape is None):
            raise PacmanValueError(
                "Both shape and start must be specified together")
        if shape is not None and len(shape) != len(start):
            raise PacmanValueError(
                "Both shape and start must have the same length")

        # Number of atoms represented by this slice
        n_atoms = hi_atom - lo_atom + 1

        # The shape of the atoms in the slice is all the atoms in a line by
        # default
        if shape is None:
            shape = (n_atoms,)
            start = (lo_atom,)

        # Create the Slice object as a `namedtuple` with these pre-computed
        # values filled in.
        return super().__new__(cls, lo_atom, hi_atom, n_atoms, shape, start)

    @property
    def as_slice(self):
        # Slice for accessing arrays of values
        return slice(self.lo_atom, self.hi_atom + 1)

    def get_slice(self, n):
        """ Get a slice in the n-th dimension

        :param int n: The 0-indexed dimension to get the shape of
        """
        if n < 0 or n > len(self.shape):
            raise IndexError(f"{n} is invalid for slice with {len(self.shape)}"
                             " dimensions")
        return slice(self.start[n], self.shape[n])
