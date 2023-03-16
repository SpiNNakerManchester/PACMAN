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
from pacman.model.graphs.common import MDSlice


class TestSlice(unittest.TestCase):
    """Tests that Slices expose the correct options and are immutable."""

    def setUp(self):
        unittest_setup()

    def test_2d(self):
        s = MDSlice(0, 8, (3, 3), (0, 0), (6, 6))
        self.assertEqual(9, s.n_atoms)  # 10 - 0 + 1
        self.assertEqual(0, s.lo_atom)  # As specified
        self.assertEqual(8, s.hi_atom)  # As specified
        self.assertEqual((3, 3), s.shape)
        self.assertEqual((0, 0), s.start)
        self.assertListEqual([0, 1, 2, 6, 7, 8, 12, 13, 14],
                             list(s.get_raster_ids((6,6))))
        self.assertListEqual([0, 1, 2, 6, 7, 8, 12, 13, 14],
                             list(s.get_raster_ids()))
        self.assertEqual(s.slices, (slice(0, 3),slice(0, 3)))
        self.assertEqual("0(6, 6)(0:3)(0:3)", str(s))
        s2 = MDSlice.from_string(str(s))
        self.assertEqual(s, s2)

    def test_2a(self):
        s = MDSlice(36, 44, (3, 3), (0, 6), (6, 12))
        self.assertEqual(9, s.n_atoms)  # 10 - 0 + 1
        self.assertEqual(36, s.lo_atom)  # As specified
        self.assertEqual(44, s.hi_atom)  # As specified
        self.assertEqual((3, 3), s.shape)
        self.assertEqual((0, 6), s.start)
        self.assertListEqual([36, 37, 38, 42, 43, 44, 48, 49, 50],
                             list(s.get_raster_ids((6,12))))
        self.assertListEqual([36, 37, 38, 42, 43, 44, 48, 49, 50],
                             list(s.get_raster_ids()))
        self.assertEqual(s.slices, (slice(0, 3), slice(6, 9)))
        self.assertEqual("36(6, 12)(0:3)(6:9)", str(s))
        s2 = MDSlice.from_string(str(s))
        self.assertEqual(s, s2)

    def test_2b(self):
        s = MDSlice(9, 17, (3, 3), (3, 0), (6,12))
        self.assertEqual(9, s.n_atoms)  # 10 - 0 + 1
        self.assertEqual(9, s.lo_atom)  # As specified
        self.assertEqual(17, s.hi_atom)  # As specified
        self.assertEqual((3, 3), s.shape)
        self.assertEqual((3, 0), s.start)
        self.assertEqual(s.slices, (slice(3, 6), slice(0, 3)))
        self.assertEqual("9(6, 12)(3:6)(0:3)", str(s))
        self.assertListEqual([3, 4, 5, 9, 10, 11, 15, 16, 17],
                             list(s.get_raster_ids((6,12))))
        self.assertListEqual([3, 4, 5, 9, 10, 11, 15, 16, 17],
                             list(s.get_raster_ids()))
        s2 = MDSlice.from_string(str(s))
        self.assertEqual(s, s2)

    def test_3b(self):
        s = MDSlice(432, 455, (2, 3, 4), (6, 9, 16), (9, 15, 20))
        self.assertEqual(24, s.n_atoms)  # 10 - 0 + 1
        self.assertEqual(432, s.lo_atom)  # As specified
        self.assertEqual(455, s.hi_atom)  # As specified
        self.assertEqual((2, 3, 4), s.shape)
        self.assertEqual((6, 9, 16), s.start)
        self.assertEqual(s.slices, (slice(6, 8), slice(9, 12), slice(16, 20)))
        self.assertEqual("432(9, 15, 20)(6:8)(9:12)(16:20)", str(s))
        self.assertListEqual([2247, 2248, 2256, 2257, 2265, 2266,
                               2382, 2383, 2391, 2392, 2400, 2401,
                               2517, 2518, 2526, 2527, 2535, 2536,
                               2652, 2653, 2661, 2662, 2670, 2671],
                             list(s.get_raster_ids((9, 15, 20))))
        self.assertListEqual([2247, 2248, 2256, 2257, 2265, 2266,
                               2382, 2383, 2391, 2392, 2400, 2401,
                               2517, 2518, 2526, 2527, 2535, 2536,
                               2652, 2653, 2661, 2662, 2670, 2671],
                             list(s.get_raster_ids()))
        s2 = MDSlice.from_string(str(s))
        self.assertEqual(s, s2)
