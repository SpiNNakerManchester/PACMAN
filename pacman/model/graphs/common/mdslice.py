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
from __future__ import annotations
from typing import Any, Tuple, Union
import numpy
from numpy.typing import NDArray
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanValueError
from .slice import Slice


class MDSlice(Slice):
    """
    Represents a multi-dimensional slice of a vertex.
    """

    __slots__ = ("_shape", "_start", "_atoms_shape")

    def __init__(
            self, lo_atom: int, hi_atom: int, shape: Tuple[int, ...],
            start: Tuple[int, ...], atoms_shape: Tuple[int, ...]):
        """
        :param lo_atom: Index of the lowest atom to represent.
        :param hi_atom: Index of the highest atom to represent.
        :param shape: The size of each dimension in the slice.
        :param start:
            The offset to the start index along each dimension.
        :param atoms_shape: The shape of atoms (?)
        :raises PacmanValueError: If the bounds of the slice are invalid.
        """
        super().__init__(lo_atom, hi_atom)

        # The shape of the atoms in the slice is all the atoms in a line by
        if shape is None:
            raise PacmanValueError(
                "shape must be specified")
        if start is None:
            raise PacmanValueError(
                "start must be specified")
        if len(shape) != len(start):
            raise PacmanValueError(
                "Both shape and start must have the same length")
        self._shape = tuple(shape)
        self._start = tuple(start)
        self._atoms_shape = tuple(atoms_shape)

    @property
    @overrides(Slice.hi_atom)
    def hi_atom(self) -> int:
        raise NotImplementedError(
            "hi_atom does not work for multi dimensional slices")

    @property
    @overrides(Slice.shape)
    def shape(self) -> Tuple[int, ...]:
        return self._shape

    @property
    @overrides(Slice.start)
    def start(self) -> Tuple[int, ...]:
        return self._start

    @overrides(Slice.as_slice)
    def as_slice(self) -> slice:
        raise NotImplementedError(
            "as slice does not work for multi dimensional slices")

    @overrides(Slice.get_slice, extend_doc=False)
    def get_slice(self, n: int) -> slice:
        """
        Get a slice in the `n`'Th dimension

        :param n: The 0-indexed dimension to get the shape of
        :returns: A 1D slice
        """
        try:
            return slice(self.start[n], self.start[n] + self.shape[n])
        except IndexError as exc:
            raise IndexError(f"{n} is invalid for slice with {len(self.shape)}"
                             " dimensions") from exc

    @property
    @overrides(Slice.dimension)
    def dimension(self) -> Tuple[slice, ...]:
        return tuple(self.get_slice(n) for n in range(len(self.shape)))

    @property
    @overrides(Slice.end)
    def end(self) -> Tuple[int, ...]:
        return tuple((numpy.array(self.start) + numpy.array(self.shape)) - 1)

    @overrides(Slice.get_ids_as_slice_or_list)
    def get_ids_as_slice_or_list(self) -> numpy.ndarray:
        return self.get_raster_ids()

    @overrides(Slice.get_raster_ids)
    def get_raster_ids(self) -> NDArray[numpy.integer]:
        slices = tuple(self.get_slice(n)
                       for n in reversed(range(len(self.start))))
        ids = numpy.arange(numpy.prod(self._atoms_shape)).reshape(
            tuple(reversed(self._atoms_shape)))
        return ids[slices].flatten()

    def __str__(self) -> str:
        value = ""
        for a_slice in self.dimension:
            value += f"({a_slice.start}:{a_slice.stop})"
        return f"{self.lo_atom}{self._atoms_shape}{value}"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MDSlice):
            return False
        if not super().__eq__(other):
            return False
        return self._atoms_shape == other._atoms_shape

    def __hash__(self) -> int:
        # Slices will generally only be hashed in sets for the same Vertex
        return self._lo_atom

    @classmethod
    @overrides(Slice.from_string, extend_doc=False)
    def from_string(cls, as_str: str) -> Union[MDSlice, Slice]:
        """
        Convert the string form of a :py:class:`MDSlice` into an object
        instance.

        :param as_str: The string to parse
        :returns: Slice described by the string
        """
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

    @overrides(Slice.get_relative_indices)
    def get_relative_indices(self, app_vertex_indices: NDArray[numpy.integer]
                             ) -> NDArray[numpy.integer]:
        n_dims = len(self._atoms_shape)
        remainders = app_vertex_indices
        cum_last_core = 1
        rel_index = numpy.zeros(len(app_vertex_indices))
        for n in range(n_dims):
            # Work out the index in this dimension
            global_index_d = remainders % self._atoms_shape[n]

            # Work out the index in this dimension relative to the core start
            rel_index_d = global_index_d - self._start[n]

            # Update the total relative index using the position in this
            # dimension
            rel_index += rel_index_d * cum_last_core

            # Prepare for next round of the loop by removing what we used
            # of the global index and remembering the sizes in this
            # dimension
            remainders = remainders // self._atoms_shape[n]
            cum_last_core *= self._shape[n]

        return rel_index.astype(numpy.uint32)

    @overrides(Slice.get_raster_indices)
    def get_raster_indices(self, relative_indices: NDArray[numpy.integer]
                           ) -> NDArray[numpy.integer]:
        n_dims = len(self._atoms_shape)
        remainders = relative_indices
        cum_last_size = 1
        global_index = numpy.zeros(len(relative_indices), dtype=int)
        for n in range(n_dims):
            # Work out the local index in this dimension
            local_index_d = remainders % self._shape[n]

            # Work out the global index in this dimension
            global_index_d = local_index_d + self._start[n]

            # Update the total global index using the position in this
            # dimension
            global_index += global_index_d * cum_last_size

            # Prepare for next round of the loop by removing what we used
            # of the local index and remembering the sizes in this dimension
            remainders = remainders // self._shape[n]
            cum_last_size *= self._atoms_shape[n]

        return global_index
