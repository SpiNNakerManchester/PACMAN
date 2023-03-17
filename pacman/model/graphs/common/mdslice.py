# Copyright (c) 2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanValueError
from .slice import Slice


class MDSlice(Slice):
    """ Represents a Multi Dimension slice of a vertex.

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

    __slots__ = ["_shape", "_start", "_atoms_shape"]

    def __init__(self, lo_atom, hi_atom, shape, start, atoms_shape):
        """ Create a new Mutile dimensional Slice object.

        :param int lo_atom: Index of the lowest atom to represent.
        :param int hi_atom: Index of the highest atom to represent.
        :raises PacmanValueError: If the bounds of the slice are invalid.
        """
        super().__init__(lo_atom, hi_atom)

        # The shape of the atoms in the slice is all the atoms in a line by
        if shape is None:
            raise PacmanValueError(
                "shape must be specified if start is specified")
        if start is None:
            raise PacmanValueError(
                "start must be specified if shape is specified")
        if len(shape) != len(start):
            raise PacmanValueError(
                "Both shape and start must have the same length")
        self._shape = shape
        self._start = start
        self._atoms_shape = atoms_shape

    @property
    @overrides(Slice.hi_atom)
    def hi_atom(self):
        # Should go pop here
        return super().hi_atom

    @property
    @overrides(Slice.shape)
    def shape(self):
        return self._shape

    @property
    @overrides(Slice.start)
    def start(self):
        return self._start

    @property
    @overrides(Slice.as_slice)
    def as_slice(self):
        # Should go pop here
        return super().as_slice

    @overrides(Slice.get_slice)
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
    @overrides(Slice.slices)
    def slices(self):
        """ Get slices for every dimension

        :rtype: tuple(slice)
        """
        return tuple(self.get_slice(n) for n in range(len(self.shape)))

    @property
    @overrides(Slice.end)
    def end(self):
        """ The end positions of the slice in each dimension
        """
        return tuple((numpy.array(self.start) + numpy.array(self.shape)) - 1)

    @overrides(Slice.get_ids_as_slice_or_list)
    def get_ids_as_slice_or_list(self):
        return self.get_raster_ids()

    @overrides(Slice.get_raster_ids)
    def get_raster_ids(self):
        """ Get the IDs of the atoms in the slice as they would appear in a
            "raster scan" of the atoms over the whole shape.

        :return: A list of the global raster IDs of the atoms in this slice
        """
        slices = tuple(self.get_slice(n)
                       for n in reversed(range(len(self.start))))
        ids = numpy.arange(numpy.prod(self._atoms_shape)).reshape(
            tuple(reversed(self._atoms_shape)))
        return ids[slices].flatten()

    def __str__(self):
        value = ""
        for a_slice in self.slices:
            value += f"({a_slice.start}:{a_slice.stop})"
        return f"{self.lo_atom}{self._atoms_shape}{value}"

    def __eq__(self, other):
        if not isinstance(other, MDSlice):
            return False
        if not super().__eq__(other):
            return False
        return self._atoms_shape == other._atoms_shape

    def __hash__(self):
        # Slices will generally only be hashed in sets for the same Vertex
        return self._lo_atom

    @classmethod
    @overrides(Slice.from_string)
    def from_string(cls, as_str):
        if as_str[0] == "(":
            return Slice.from_string(as_str)
        parts = as_str.split("(")
        lo_atom = int(parts[0])
        shape = []
        start = []
        size = 1
        atoms_shape = tuple(int(sub) for sub in parts[1][:-1].split(","))
        for part in parts[2:]:
            subs = part.split(":")
            begin = int(subs[0])
            atoms = int(subs[1][:-1]) - begin
            size *= atoms
            shape.append(atoms)
            start.append(begin)
        return MDSlice(
            lo_atom, lo_atom + size - 1, tuple(shape), tuple(start),
            atoms_shape)
