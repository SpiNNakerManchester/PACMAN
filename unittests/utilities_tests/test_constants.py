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
