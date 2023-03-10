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
from spinn_utilities.abstract_base import AbstractBase, abstractproperty
import math
from pacman.exceptions import PacmanConfigurationException
from pacman.utilities.utility_calls import get_n_bits
from pacman.utilities.constants import BITS_IN_KEY
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.model.graphs.common import MDSlice


class Abstract2DDeviceVertex(object, metaclass=AbstractBase):
    """ A helper for 2D input devices.  Note that this assumes that
        the input keys will contain a field for each of the X and Y dimensions
        with X field in the LSBs and the Y field in the next adjacent bits.  If
        the fields are in different places, override the methods:
        _source_x_shift, _source_y_shift, _source_x_mask and _source_y_mask.
        If the key has bits in addition to the X and Y values, you can also
        override _key_shift.
    """

    @abstractproperty
    def _width(self):
        """ The width of the device

        :rtype: int
        """

    @abstractproperty
    def _height(self):
        """ The height of the device

        :rtype: int
        """

    @abstractproperty
    def _sub_width(self):
        """ The width of the sub-rectangles to divide the input into

        :rtype: int
        """

    @abstractproperty
    def _sub_height(self):
        """ The height of the sub-rectangles to divide the input into

        :rtype: int
        """

    def __is_power_of_2(self, v):
        """ Determine if a value is a power of 2

        :param int v: The value to test
        :rtype: bool
        """
        return (v & (v - 1) == 0) and (v != 0)

    def _verify_sub_size(self):
        """ Ensure the sub width and height are within restrictions
        """
        if not self.__is_power_of_2(self._sub_width):
            raise PacmanConfigurationException(
                f"sub_width ({self._sub_width}) must be a power of 2")
        if not self.__is_power_of_2(self._sub_height):
            raise PacmanConfigurationException(
                f"sub_height ({self._sub_height}) must be a power of 2")
        if self._sub_width > self._width:
            raise PacmanConfigurationException(
                f"sub_width ({self._sub_width}) must not be greater than "
                f"width ({self._width})")
        if self._sub_height > self._height:
            raise PacmanConfigurationException(
                f"sub_height ({self._sub_height}) must not be greater than "
                f"height ({self._height})")

    @property
    def _n_sub_rectangles(self):
        """ The number of sub-rectangles the device is made up of

        :rtype: int
        """
        return (int(math.ceil(self._width / self._sub_width)) *
                int(math.ceil(self._height / self._sub_height)))

    def _sub_square_from_index(self, index):
        """ Work out the x and y components of the index

        :param int index: The index of the sub square
        :rtype: tuple(int, int)
        """
        n_squares_per_row = int(math.ceil(
            self._width / self._sub_width))
        x_index = index % n_squares_per_row
        y_index = index // n_squares_per_row

        # Return the information
        return x_index, y_index

    def _get_slice(self, index):
        """ Get the slice for the given machine vertex index

        :param int index: The machine vertex index
        :rtype: Slice
        """
        x_index, y_index = self._sub_square_from_index(index)
        lo_atom_x = x_index * self._sub_width
        lo_atom_y = y_index * self._sub_height
        n_atoms_per_subsquare = self._sub_width * self._sub_height
        lo_atom = index * n_atoms_per_subsquare
        hi_atom = (lo_atom + n_atoms_per_subsquare) - 1
        return MDSlice(
            lo_atom, hi_atom, (self._sub_width, self._sub_height),
            (lo_atom_x, lo_atom_y))

    def _get_key_and_mask(self, base_key, index):
        """ Get the key and mask of the given machine vertex index

        :param int base_key: The unshifted key to use
        :param int index: The machine vertex index
        :rtype: BaseKeyAndMask
        """
        x_index, y_index = self._sub_square_from_index(index)
        key_bits = base_key << self._key_shift
        key = (key_bits +
               (y_index << self._y_index_shift) +
               (x_index << self._x_index_shift))
        return BaseKeyAndMask(key, self._mask)

    @property
    def _mask(self):
        """ The mask to be used for the key

        :rtype: int
        """
        n_key_bits = BITS_IN_KEY - self._key_shift
        key_mask = (1 << n_key_bits) - 1
        sub_x_mask = (1 << self._sub_x_bits) - 1
        sub_y_mask = (1 << self._sub_y_bits) - 1
        return ((key_mask << self._key_shift) +
                (sub_y_mask << self._y_index_shift) +
                (sub_x_mask << self._x_index_shift))

    @property
    def _key_fields(self):
        """ The fields in the key for X and Y

        :return: (start, size, mask, shift) for each of X and Y
        :rtype: tuple(tuple(int, int, int int), tuple(int, int, int, int))
        """
        return ((0, self._width, self._source_x_mask, self._source_x_shift),
                (0, self._height, self._source_y_mask, self._source_y_shift))

    @property
    def _x_bits(self):
        """ The number of bits to use for X

        :rtype: int
        """
        return get_n_bits(self._width)

    @property
    def _y_bits(self):
        """ The number of bits to use for Y

        :rtype: int
        """
        return get_n_bits(self._height)

    @property
    def _sub_x_bits(self):
        """ The number of bits to use for the X coordinate of a sub-rectangle

        :rtype: int
        """
        n_per_row = int(math.ceil(self._width / self._sub_width))
        return get_n_bits(n_per_row)

    @property
    def _sub_y_bits(self):
        """ The number of bits to use for the Y coordinate of a sub-rectangle

        :rtype: int
        """
        n_per_col = int(math.ceil(self._height / self._sub_height))
        return get_n_bits(n_per_col)

    @property
    def _x_index_shift(self):
        """ The shift to apply to the key to get the sub-X coordinate

        :rtype: int
        """
        return self._source_x_shift + (self._x_bits - self._sub_x_bits)

    @property
    def _y_index_shift(self):
        """ The shift to apply to the key to get the sub-Y coordinate

        :rtype: int
        """
        return self._source_y_shift + (self._y_bits - self._sub_y_bits)

    @property
    def _source_x_mask(self):
        """ The mask to apply to the key *before* shifting to get the
            X coordinate

        :rtype: int
        """
        return (1 << self._x_bits) - 1

    @property
    def _source_x_shift(self):
        """ The shift to apply to the key *after* masking to get the
            X coordinate

        :rtype: int
        """
        return 0

    @property
    def _source_y_mask(self):
        """ The mask to apply to the key *before* shifting to get the
            Y coordinate

        :rtype: int
        """
        return ((1 << self._y_bits) - 1) << self._x_bits

    @property
    def _source_y_shift(self):
        """ The shift to apply to the key *after* masking to get the
            Y coordinate

        :rtype: int
        """
        return self._x_bits

    @property
    def _key_shift(self):
        """ The shift to apply to the key to get the base key

        :rtype: int
        """
        return self._y_bits + self._x_bits
