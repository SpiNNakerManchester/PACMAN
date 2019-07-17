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

"""
tests for slice
"""
import unittest
from pacman.exceptions import PacmanValueError
from pacman.model.graphs.common import Slice


class TestSliceFunctions(unittest.TestCase):
    """
    slice function tests
    """

    def test_create_slice_valid(self):
        """
        test creating a empty slice
        """
        Slice(0, 1)

    def test_slice_invalid_neg(self):
        """
        test that a invalid slice of negative value generates an error
        """
        self.assertRaises(PacmanValueError, Slice, -2, 0)

    def test_slice_invalid_lo_higher_than_hi(self):
        """
        test that a invalid slice generates an error
        """
        self.assertRaises(PacmanValueError, Slice, 2, 0)


if __name__ == '__main__':
    unittest.main()
