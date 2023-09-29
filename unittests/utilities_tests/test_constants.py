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
from pacman.utilities import constants


class TestConstants(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_edges_enum(self):
        self.assertEqual(constants.EDGES.EAST.value, 0)
        self.assertEqual(constants.EDGES.NORTH_EAST.value, 1)
        self.assertEqual(constants.EDGES.NORTH.value, 2)
        self.assertEqual(constants.EDGES.WEST.value, 3)
        self.assertEqual(constants.EDGES.SOUTH_WEST.value, 4)
        self.assertEqual(constants.EDGES.SOUTH.value, 5)


if __name__ == '__main__':
    unittest.main()
