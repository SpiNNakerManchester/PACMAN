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


class TestMD_Slice(unittest.TestCase):
    """Tests that Slices expose the correct options and are immutable."""

    def setUp(self):
        unittest_setup()

    def test_2d(self):
        s = MDSlice(0, 8, (3, 3), (0, 0))
        self.assertEqual("0(0:3)(0:3)", str(s))
        s2 = MDSlice.from_string(str(s))
        self.assertEqual(s, s2)

    def test_2a(self):
        s = MDSlice(36, 44, (3, 3), (0, 6))
        self.assertEqual("36(0:3)(6:9)", str(s))
        s2 = MDSlice.from_string(str(s))
        self.assertEqual(s, s2)

    def test_2b(self):
        s = MDSlice(9, 17, (3, 3), (3, 0))
        self.assertEqual("9(3:6)(0:3)", str(s))
        s2 = MDSlice.from_string(str(s))
        self.assertEqual(s, s2)

    def test_3b(self):
        s = MDSlice(432, 455, (2, 3, 4), (6, 9, 16))
        self.assertEqual("432(6:8)(9:12)(16:20)", str(s))
        s2 = MDSlice.from_string(str(s))
        self.assertEqual(s, s2)
