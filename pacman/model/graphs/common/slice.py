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
from __future__ import annotations
from typing import Tuple, Union
import numpy
from numpy.typing import NDArray
from pacman.exceptions import PacmanValueError, PacmanTypeError


class Slice(object):
    """
    Represents a simple single-dimensional slice of a vertex.

    .. note::
        Multi-dimensional slices are supported by :py:class:`MDSlice`.
    """

    __slots__ = ("_lo_atom", "_n_atoms")

    def __init__(self, lo_atom: int, hi_atom: int):
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
                f'hi_atom {hi_atom:d} < lo_atom {lo_atom:d}')

        self._lo_atom = lo_atom
        # Number of atoms represented by this slice
        self._n_atoms = hi_atom - lo_atom + 1

    @property
    def lo_atom(self) -> int:
        """
        The lowest atom represented in the slice.

        :rtype: int
        """
        return self._lo_atom

    @property
    def hi_atom(self) -> int:
        """
        The highest atom represented in the slice.

        .. note::
            Use of this method is *not* recommended.
            It fails for multi-dimensional slices and may be removed

        :rtype: int
        """
        return self._lo_atom + self._n_atoms - 1

    @property
    def n_atoms(self) -> int:
        """
        The number of atoms represented by the slice.

        :rtype: int
        """
        return self._n_atoms

    @property
    def shape(self) -> Tuple[int, ...]:
        """
        The shape of the atoms over multiple dimensions.
        By default the shape will be 1-dimensional.

        :rtype: tuple(int,...)
        """
        return (self._n_atoms, )

    @property
    def start(self) -> Tuple[int, ...]:
        """
        The start coordinates of the slice.
        By default this will be `lo_atom` in 1 dimension.

        :rtype: tuple(int,...)
        """
        return (self._lo_atom, )

    @property
    def as_slice(self) -> slice:
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

    def get_slice(self, n: int) -> slice:
        """
        Get a slice in the `n`'Th dimension.

        :param int n: Must be 0
        :type: slice
        """
        if n == 0:
            return slice(self._lo_atom, self._lo_atom + self._n_atoms)
        raise IndexError(f"{n} is invalid for a 1 dimension Slice ")

    @property
    def dimension(self) -> Tuple[slice, ...]:
        """
        Get directions or edges as slices for every dimension

        This is the width and if available height, depth, etc., of the
        Slice/Grid as represented as slices form the origin along in that
        direction.

        :rtype: tuple(slice, ...)
        """
        return (slice(self._lo_atom, self._lo_atom + self._n_atoms), )

    @property
    def end(self) -> Tuple[int, ...]:
        """
        The end positions of the slice in each dimension

        :rtype: tuple(int, ...)
        """
        return (self._lo_atom + self._n_atoms, )

    def get_ids_as_slice_or_list(self) -> Union[slice, numpy.ndarray]:
        """
        Returns the IDs as a built-in slice if possible,
        otherwise as a list of IDs.

        :return: a slice or list of IDs
        :rtype: slice or list(int)
        """
        return slice(self._lo_atom, self._lo_atom + self._n_atoms)

    def get_raster_ids(self) -> NDArray[numpy.integer]:
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
    def from_string(cls, as_str: str) -> Slice:
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

    def get_relative_indices(self, app_vertex_indices: NDArray[numpy.integer]
                             ) -> NDArray[numpy.integer]:
        """
        Convert from raster indices to slice-level indices.

        Note that no checking is done on the given indices; they should be
        within this slice!

        :param numpy.ndarray app_vertex_indices:
            The raster application vertex indices to convert
        :return: The local core-level indices relative to this slice
        """
        return app_vertex_indices - self._lo_atom

    def get_raster_indices(self, relative_indices: NDArray[numpy.integer]
                           ) -> NDArray[numpy.integer]:
        """
        Convert from slice-level indices to raster indices.

        Note that no checking is done on the given indices; they should be
        within this slice!

        :param numpy.ndarray relative_indices:
            The local core-level indices relative to this slice
        :return: The raster application vertex indices
        """
        return relative_indices + self._lo_atom
