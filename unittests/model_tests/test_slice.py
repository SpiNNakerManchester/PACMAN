# Copyright (c) 2015 The University of Manchester
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

import unittest
from pacman.config_setup import unittest_setup
from pacman.model.graphs.common import Slice


class TestSlice(unittest.TestCase):
    """Tests that Slices expose the correct options and are immutable."""

    def setUp(self):
        unittest_setup()

    def test_basic(self):
        s = Slice(0, 10)
        self.assertEqual(11, s.n_atoms)  # 10 - 0 + 1
        self.assertEqual(0, s.lo_atom)  # As specified
        self.assertEqual(10, s.hi_atom)  # As specified
        assert s.as_slice == slice(0, 11)  # Slice object supported by arrays
        self.assertListEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                             list(s.get_raster_ids((20, ))))
        self.assertEqual(s.slices, (slice(0, 11),))
        self.assertEqual("(0:10)", str(s))
        s2 = Slice.from_string(str(s))
        self.assertEqual((11, ), s.shape)
        self.assertEqual((0, ), s.start)
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
        s = Slice(4, 4)
        self.assertEqual(1, s.n_atoms)  # 10 - 0 + 1
        self.assertEqual(4, s.lo_atom)  # As specified
        self.assertEqual(4, s.hi_atom)  # As specified
        assert s.as_slice == slice(4, 5)  # Slice object supported by arrays
        self.assertListEqual([4], list(s.get_raster_ids((20,))))
        self.assertEqual(s.slices, (slice(4, 5),))
        self.assertEqual("(4:4)", str(s))
        s2 = Slice.from_string(str(s))
        self.assertEqual((1, ), s.shape)
        self.assertEqual((4, ), s.start)
        self.assertEqual(s, s2)

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
        self.assertEqual(9, s.n_atoms)  # 10 - 0 + 1
        self.assertEqual(0, s.lo_atom)  # As specified
        self.assertEqual(8, s.hi_atom)  # As specified
        self.assertEqual((3, 3), s.shape)
        self.assertEqual((0, 0), s.start)
        self.assertListEqual([0, 1, 2, 6, 7, 8, 12, 13, 14],
                             list(s.get_raster_ids((6,6))))
        self.assertEqual(s.slices, (slice(0, 3),slice(0, 3)))
        self.assertEqual("0(0:3)(0:3)", str(s))
        s2 = Slice.from_string(str(s))
        self.assertEqual(s, s2)

    def test_2a(self):
        s = Slice(36, 44, (3, 3), (0, 6))
        self.assertEqual(9, s.n_atoms)  # 10 - 0 + 1
        self.assertEqual(36, s.lo_atom)  # As specified
        self.assertEqual(44, s.hi_atom)  # As specified
        self.assertEqual((3, 3), s.shape)
        self.assertEqual((0, 6), s.start)
        self.assertListEqual([36, 37, 38, 42, 43, 44, 48, 49, 50],
                             list(s.get_raster_ids((6,12))))
        self.assertEqual(s.slices, (slice(0, 3), slice(6, 9)))
        self.assertEqual("36(0:3)(6:9)", str(s))
        s2 = Slice.from_string(str(s))
        self.assertEqual(s, s2)

    def test_2b(self):
        s = Slice(9, 17, (3, 3), (3, 0))
        self.assertEqual(9, s.n_atoms)  # 10 - 0 + 1
        self.assertEqual(9, s.lo_atom)  # As specified
        self.assertEqual(17, s.hi_atom)  # As specified
        self.assertEqual((3, 3), s.shape)
        self.assertEqual((3, 0), s.start)
        self.assertEqual(s.slices, (slice(3, 6), slice(0, 3)))
        self.assertEqual("9(3:6)(0:3)", str(s))
        self.assertListEqual([3, 4, 5, 9, 10, 11, 15, 16, 17],
                             list(s.get_raster_ids((6,12))))
        s2 = Slice.from_string(str(s))
        self.assertEqual(s, s2)

    def test_3b(self):
        s = Slice(432, 455, (2, 3, 4), (6, 9, 16))
        self.assertEqual(24, s.n_atoms)  # 10 - 0 + 1
        self.assertEqual(432, s.lo_atom)  # As specified
        self.assertEqual(455, s.hi_atom)  # As specified
        self.assertEqual((2, 3, 4), s.shape)
        self.assertEqual((6, 9, 16), s.start)
        self.assertEqual(s.slices, (slice(6, 8), slice(9, 12), slice(16, 20)))
        self.assertEqual("432(6:8)(9:12)(16:20)", str(s))
        self.assertListEqual([2247, 2248, 2256, 2257, 2265, 2266,
                               2382, 2383, 2391, 2392, 2400, 2401,
                               2517, 2518, 2526, 2527, 2535, 2536,
                               2652, 2653, 2661, 2662, 2670, 2671],
                             list(s.get_raster_ids((9, 15, 20))))
        s2 = Slice.from_string(str(s))
        self.assertEqual(s, s2)
