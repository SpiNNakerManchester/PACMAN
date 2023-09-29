# Copyright (c) 2017 The University of Manchester
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
from pacman.model.graphs.common import ChipAndCore


class TestPlacementConstraints(unittest.TestCase):
    """ Tester for ChipAndCore
    """

    def setUp(self):
        unittest_setup()

    def test_chip_and_core_constraint(self):
        c1 = ChipAndCore(1, 2)
        self.assertEqual(c1.x, 1)
        self.assertEqual(c1.y, 2)
        self.assertEqual(c1.p, None)
        self.assertEqual(c1, ChipAndCore(1, 2))
        self.assertEqual(str(c1), 'X:1,Y2')
        c2 = ChipAndCore(2, 1)
        c3 = ChipAndCore(1, 2, 3)
        self.assertNotEqual(c1, c2)
        self.assertNotEqual(c1, c3)
        self.assertNotEqual(c1, "1.2.3.4")
        d = {}
        d[c1] = 1
        d[c2] = 2
        d[c3] = 3
        self.assertEqual(len(d), 3)
