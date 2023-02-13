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

"""
tests for slice
"""
import unittest
from pacman.config_setup import unittest_setup
from pacman.exceptions import PacmanValueError
from pacman.model.graphs.common import Slice


class TestSliceFunctions(unittest.TestCase):
    """
    slice function tests
    """

    def setUp(self):
        unittest_setup()

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
