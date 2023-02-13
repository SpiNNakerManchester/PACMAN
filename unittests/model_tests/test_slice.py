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

import unittest
from pacman.config_setup import unittest_setup
from pacman.model.graphs.common import Slice


class TestSlice(unittest.TestCase):
    """Tests that Slices expose the correct options and are immutable."""

    def setUp(self):
        unittest_setup()

    def test_basic(self):
        s = Slice(0, 10)
        assert s.n_atoms == 11  # 10 - 0 + 1
        assert s.lo_atom == 0   # As specified
        assert s.hi_atom == 10  # As specified
        assert s.as_slice == slice(0, 11)  # Slice object supported by arrays
        self.assertEqual("(0:10)", str(s))
        s2 = Slice.from_string(str(s))
        self.assertEqual(s, s2)

    def test_check_lo_atom_sanity(self):
        # Check for value sanity
        with self.assertRaises(ValueError):
            # Check for negative atom
            Slice(-1, 10)

    def test_check_lo_atom_int(self):
        # Check for value sanity
        with self.assertRaises(Exception):
            # Check for int atom
            Slice("1", 10)

    def test_check_hi_atom_sanity(self):
        with self.assertRaises(ValueError):
            # Check for slice which goes backwards
            Slice(5, 4)

    def test_check_hi_atom_int(self):
        # Check for value sanity
        with self.assertRaises(Exception):
            # Check for int atom
            Slice(1, "10")

    def test_equal_hi_lo_atoms(self):
        # This should be fine...
        Slice(4, 4)

    def test_immutability_lo_atom(self):
        s = Slice(0, 10)
        with self.assertRaises(AttributeError):
            s.lo_atom = 3

    def test_immutability_hi_atom(self):
        s = Slice(0, 10)
        with self.assertRaises(AttributeError):
            s.hi_atom = 3

    def test_immutability_n_atoms(self):
        s = Slice(0, 10)
        with self.assertRaises(AttributeError):
            s.n_atoms = 3

    def test_immutability_as_slice(self):
        s = Slice(0, 10)
        with self.assertRaises(AttributeError):
            s.as_slice = slice(2, 10)

    def test_2d(self):
        s = Slice(0, 8, (3, 3), (0, 0))
        self.assertEqual("0(0:3)(0:3)", str(s))
        s2 = Slice.from_string(str(s))
        self.assertEqual(s, s2)

    def test_2a(self):
        s = Slice(36, 44, (3, 3), (0, 6))
        self.assertEqual("36(0:3)(6:9)", str(s))
        s2 = Slice.from_string(str(s))
        self.assertEqual(s, s2)

    def test_2b(self):
        s = Slice(9, 17, (3, 3), (3, 0))
        self.assertEqual("9(3:6)(0:3)", str(s))
        s2 = Slice.from_string(str(s))
        self.assertEqual(s, s2)

    def test_3b(self):
        s = Slice(432, 455, (2, 3, 4), (6, 9, 16))
        self.assertEqual("432(6:8)(9:12)(16:20)", str(s))
        s2 = Slice.from_string(str(s))
        self.assertEqual(s, s2)
