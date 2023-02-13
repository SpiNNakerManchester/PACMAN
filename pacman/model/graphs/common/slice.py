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

import collections
import numpy
from pacman.exceptions import PacmanValueError, PacmanTypeError


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
            raise PacmanTypeError("lo atom needs to be a int")
        if not isinstance(hi_atom, int):
            raise PacmanTypeError("hi atom needs to be a int")

        if lo_atom < 0:
            raise PacmanValueError('lo_atom < 0')
        if hi_atom < lo_atom:
            raise PacmanValueError(
                'hi_atom {:d} < lo_atom {:d}'.format(hi_atom, lo_atom))

        # Number of atoms represented by this slice
        n_atoms = hi_atom - lo_atom + 1

        # The shape of the atoms in the slice is all the atoms in a line by
        # default
        if shape is None:
            if start is not None:
                raise PacmanValueError(
                    "shape must be specified if start is specified")
            shape = (n_atoms,)
            start = (lo_atom,)
        else:
            if start is None:
                raise PacmanValueError(
                    "start must be specified if shape is specified")
            if len(shape) != len(start):
                raise PacmanValueError(
                    "Both shape and start must have the same length")

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
        :type: slice
        """
        try:
            return slice(self.start[n], self.start[n] + self.shape[n])
        except IndexError as exc:
            raise IndexError(f"{n} is invalid for slice with {len(self.shape)}"
                             " dimensions") from exc

    @property
    def slices(self):
        """ Get slices for every dimension

        :rtype: tuple(slice)
        """
        return tuple(self.get_slice(n) for n in range(len(self.shape)))

    @property
    def end(self):
        """ The end positions of the slice in each dimension
        """
        return tuple((numpy.array(self.start) + numpy.array(self.shape)) - 1)

    def get_raster_ids(self, atoms_shape):
        """ Get the IDs of the atoms in the slice as they would appear in a
            "raster scan" of the atoms over the whole shape.

        :param tuple(int) atoms_shape:
            The size of each dimension of the whole shape
        :return: A list of the global raster IDs of the atoms in this slice
        """
        slices = tuple(self.get_slice(n)
                       for n in reversed(range(len(self.start))))
        ids = numpy.arange(numpy.prod(atoms_shape)).reshape(
            tuple(reversed(atoms_shape)))
        return ids[slices].flatten()

    def __str__(self):
        if len(self.shape) <= 1:
            return (f"({self.lo_atom}:{self.hi_atom})")
        value = ""
        for a_slice in self.slices:
            value += f"({a_slice.start}:{a_slice.stop})"
        return f"{self.lo_atom}{value}"

    @classmethod
    def from_string(cls, as_str):
        if as_str[0] == "(":
            parts = as_str[1:-1].split(":")
            lo_atom = int(parts[0])
            hi_atom = int(parts[1])
            return Slice(lo_atom, hi_atom)
        parts = as_str.split("(")
        lo_atom = int(parts[0])
        shape = []
        start = []
        size = 1
        for part in parts[1:]:
            subs = part.split(":")
            begin = int(subs[0])
            atoms = int(subs[1][:-1]) - begin
            size *= atoms
            shape.append(atoms)
            start.append(begin)
        return Slice(lo_atom, lo_atom + size - 1, tuple(shape), tuple(start))
