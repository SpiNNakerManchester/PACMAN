# Copyright (c) 2021 The University of Manchester
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
import math
from typing import Tuple
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.overrides import overrides
from spinn_utilities.typing.coords import XY
from pacman.exceptions import PacmanConfigurationException
from pacman.utilities.utility_calls import get_n_bits, is_power_of_2
from pacman.utilities.constants import BITS_IN_KEY
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.common import MDSlice


class Abstract2DDeviceVertex(object, metaclass=AbstractBase):
    """
    A helper for 2D input devices.

    .. note::
        This assumes that
        the input keys will contain a field for each of the X and Y dimensions
        with X field in the LSBs and the Y field in the next adjacent bits.  If
        the fields are in different places, override the methods:
        `_source_x_shift`, `_source_y_shift`, `_source_x_mask` and
        `_source_y_mask`.
        If the key has bits in addition to the X and Y values, you can also
        override `_key_shift`.
    """

    @property
    @abstractmethod
    def width(self) -> int:
        """
        The width of the device.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def height(self) -> int:
        """
        The height of the device.
       """
        raise NotImplementedError

    @property
    @abstractmethod
    def sub_width(self) -> int:
        """
        The width of the sub-rectangles to divide the input into.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def sub_height(self) -> int:
        """
        The height of the sub-rectangles to divide the input into.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    @overrides(ApplicationVertex.atoms_shape)
    def atoms_shape(self) -> Tuple[int, ...]:
        """
        The "shape" of the atoms in the vertex i.e. how the atoms are split
        between the dimensions of the vertex.  By default everything is
        1-dimensional, so the value will be a 1-tuple but can be
        overridden by a vertex that supports multiple dimensions.
        """
        raise NotImplementedError

    def _verify_sub_size(self) -> None:
        """
        Ensure the sub width and height are within restrictions.
        """
        if not is_power_of_2(self.sub_width):
            raise PacmanConfigurationException(
                f"sub_width ({self.sub_width}) must be a power of 2")
        if not is_power_of_2(self.sub_height):
            raise PacmanConfigurationException(
                f"sub_height ({self.sub_height}) must be a power of 2")
        if self.sub_width > self.width:
            raise PacmanConfigurationException(
                f"sub_width ({self.sub_width}) must not be greater than "
                f"width ({self.width})")
        if self.sub_height > self.height:
            raise PacmanConfigurationException(
                f"sub_height ({self.sub_height}) must not be greater than "
                f"height ({self.height})")

    @property
    def _n_sub_rectangles(self) -> int:
        """
        The number of sub-rectangles the device is made up of.
        """
        return (int(math.ceil(self.width / self.sub_width)) *
                int(math.ceil(self.height / self.sub_height)))

    def _sub_square_from_index(self, index: int) -> XY:
        """
        Work out the x and y components of the index.

        :param index: The index of the sub square
        """
        n_squares_per_row = int(math.ceil(
            self.width / self.sub_width))
        x_index = index % n_squares_per_row
        y_index = index // n_squares_per_row

        # Return the information
        return x_index, y_index

    def _get_slice(self, index: int) -> MDSlice:
        """
        Get the slice for the given machine vertex index.

        :param index: The machine vertex index
        """
        x_index, y_index = self._sub_square_from_index(index)
        lo_atom_x = x_index * self.sub_width
        lo_atom_y = y_index * self.sub_height
        n_atoms_per_subsquare = self.sub_width * self.sub_height
        lo_atom = index * n_atoms_per_subsquare
        hi_atom = (lo_atom + n_atoms_per_subsquare) - 1
        return MDSlice(
            lo_atom, hi_atom, (self.sub_width, self.sub_height),
            (lo_atom_x, lo_atom_y), self.atoms_shape)

    def _get_key_and_mask(self, base_key: int, index: int) -> BaseKeyAndMask:
        """
        Get the key and mask of the given machine vertex index.

        :param base_key: The key to use (not shifted)
        :param index: The machine vertex index
        """
        x_index, y_index = self._sub_square_from_index(index)
        key_bits = base_key << self._key_shift
        key = (key_bits +
               (y_index << self._y_index_shift) +
               (x_index << self._x_index_shift))
        return BaseKeyAndMask(key, self._mask)

    @property
    def _mask(self) -> int:
        """
        The mask to be used for the key.
        """
        n_key_bits = BITS_IN_KEY - self._key_shift
        key_mask = (1 << n_key_bits) - 1
        sub_x_mask = (1 << self._sub_x_bits) - 1
        sub_y_mask = (1 << self._sub_y_bits) - 1
        return ((key_mask << self._key_shift) +
                (sub_y_mask << self._y_index_shift) +
                (sub_x_mask << self._x_index_shift))

    @property
    def _x_bits(self) -> int:
        """
        The number of bits to use for X.
        """
        return get_n_bits(self.width)

    @property
    def _y_bits(self) -> int:
        """
        The number of bits to use for Y.
        """
        return get_n_bits(self.height)

    @property
    def _sub_x_bits(self) -> int:
        """
        The number of bits to use for the X coordinate of a sub-rectangle.
        """
        n_per_row = int(math.ceil(self.width / self.sub_width))
        return get_n_bits(n_per_row)

    @property
    def _sub_y_bits(self) -> int:
        """
        The number of bits to use for the Y coordinate of a sub-rectangle.
        """
        n_per_col = int(math.ceil(self.height / self.sub_height))
        return get_n_bits(n_per_col)

    @property
    def _x_index_shift(self) -> int:
        """
        The shift to apply to the key to get the sub-X coordinate.
        """
        return self._source_x_shift + (self._x_bits - self._sub_x_bits)

    @property
    def _y_index_shift(self) -> int:
        """
        The shift to apply to the key to get the sub-Y coordinate.
        """
        return self._source_y_shift + (self._y_bits - self._sub_y_bits)

    @property
    def _source_x_mask(self) -> int:
        """
        The mask to apply to the key *before* shifting to get the
        X coordinate.
        """
        return (1 << self._x_bits) - 1

    @property
    def _source_x_shift(self) -> int:
        """
        The shift to apply to the key *after* masking to get the
        X coordinate.
        """
        return 0

    @property
    def _source_y_mask(self) -> int:
        """
        The mask to apply to the key *before* shifting to get the
        Y coordinate.
        """
        return ((1 << self._y_bits) - 1) << self._x_bits

    @property
    def _source_y_shift(self) -> int:
        """
        The shift to apply to the key *after* masking to get the
        Y coordinate.
        """
        return self._x_bits

    @property
    def _key_shift(self) -> int:
        """
        The shift to apply to the key to get the base key.
        """
        return self._y_bits + self._x_bits
