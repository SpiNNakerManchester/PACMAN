# Copyright (c) 2014 The University of Manchester
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
from pacman.exceptions import PacmanValueError, PacmanTypeError


class Slice(object):
    """
    Represents a simple single-dimensional slice of a vertex.

    .. note::
        Multi-dimensional slices are supported by :py:class:`MDSlice`.
    """

    __slots__ = ["_lo_atom", "_n_atoms"]

    def __init__(self, lo_atom, hi_atom):
        """
        :param int lo_atom: Index of the lowest atom to represent.
        :param int hi_atom: Index of the highest atom to represent.
        :raises PacmanTypeError: If non-integer arguments are used.
        :raises PacmanValueError: If the bounds of the slice are invalid.
        """
        if not isinstance(lo_atom, int):
            raise PacmanTypeError("lo_atom needs to be a int")
        if not isinstance(hi_atom, int):
            raise PacmanTypeError("hi_atom needs to be a int")

        if lo_atom < 0:
            raise PacmanValueError('lo_atom < 0')
        if hi_atom < lo_atom:
            raise PacmanValueError(
                'hi_atom {:d} < lo_atom {:d}'.format(hi_atom, lo_atom))

        self._lo_atom = lo_atom
        # Number of atoms represented by this slice
        self._n_atoms = hi_atom - lo_atom + 1

    @property
    def lo_atom(self):
        """
        The lowest atom represented in the slice.

        :rtype: int
        """
        return self._lo_atom

    @property
    def hi_atom(self):
        """
        The highest atom represented in the slice.

        .. note::
            Use of this method is *not* recommended.
            It fails for multi-dimensional slices and may be removed

        :rtype: int
        """
        return self._lo_atom + self._n_atoms - 1

    @property
    def n_atoms(self):
        """
        The number of atoms represented by the slice.

        :rtype: int
        """
        return self._n_atoms

    @property
    def shape(self):
        """
        The shape of the atoms over multiple dimensions.
        By default the shape will be 1-dimensional.

        :rtype: tuple(int,...)
        """
        return (self._n_atoms, )

    @property
    def start(self):
        """
        The start coordinates of the slice.
        By default this will be `lo_atom` in 1 dimension.

        :rtype: tuple(int,...)
        """
        return (self._lo_atom,)

    @property
    def as_slice(self):
        """
        Converts the Slice to a standard slice object *if possible.*

        .. note::
            Use of this method is *not* recommended.
            It fails for multi-dimensional slices and may be removed.

        :return: a standard built-in slice object
        :rtype: slice
        :raises NotImplementedError: If called on a multi-dimensional slice
        """
        # slice for accessing arrays of values
        return slice(self._lo_atom, self._lo_atom + self._n_atoms)

    def get_slice(self, n):
        """
        Get a slice in the `n`'th dimension.

        :param int n: Must be 0
        :type: slice
        """
        if n == 0:
            return slice(self._lo_atom, self._lo_atom + self._n_atoms)
        raise IndexError(f"{n} is invalid for a 1 dimension Slice ")

    @property
    def dimension(self):
        """
        Get directions or edges as slices for every dimension

        This is the width and if available height, depth, etc., of the
        Slice/Grid as represented as slices form the origin along in that
        direction.

        :rtype: tuple(slice, ...)
        """
        return (slice(self._lo_atom, self._lo_atom + self._n_atoms), )

    @property
    def end(self):
        """
        The end positions of the slice in each dimension

        :rtype: tuple(int, ...)
        """
        return tuple(self._lo_atom + self._n_atoms)

    def get_ids_as_slice_or_list(self):
        """
        Returns the IDs as a built-in slice if possible,
        otherwise as a list of IDs.

        :return: a slice or list of IDs
        :rtype: slice or list(int)
        """
        return slice(self._lo_atom, self._lo_atom + self._n_atoms)

    def get_raster_ids(self):
        """
        Get the IDs of the atoms in the slice as they would appear in a
        "raster scan" of the atoms over the whole shape.

        :return: A list of the global raster IDs of the atoms in this slice
        :rtype: ~numpy.ndarray
        """
        return numpy.array(range(self._lo_atom, self._lo_atom + self._n_atoms))

    def __str__(self):
        return (f"({self.lo_atom}:{self.hi_atom})")

    def __eq__(self, other):
        if not isinstance(other, Slice):
            return False
        if self._lo_atom != other.lo_atom:
            return False
        # These checks are mainly to comparing to an extended slice
        if self.shape != other.shape:
            return False
        if self.start != other.start:
            return False
        return self._n_atoms == other.n_atoms

    def __hash__(self):
        # Slices will generally only be hashed in sets for the same Vertex
        return self._lo_atom

    @classmethod
    def from_string(cls, as_str):
        """
        Convert the string form of a :py:class:`Slice` into an object instance.

        :param str as_str: The string to parse
        :rtype: Slice
        """
        if as_str[0] != "(":
            raise NotImplementedError("Please use MDSlice method")

        parts = as_str[1:-1].split(":")
        lo_atom = int(parts[0])
        hi_atom = int(parts[1])
        return Slice(lo_atom, hi_atom)
