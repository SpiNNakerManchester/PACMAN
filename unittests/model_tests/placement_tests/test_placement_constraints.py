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
