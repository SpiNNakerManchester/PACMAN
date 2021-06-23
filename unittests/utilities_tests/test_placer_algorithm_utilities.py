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
from pacman.utilities.algorithm_utilities.placer_algorithm_utilities import (
    add_set)


class TestUtilities(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_add_join(self):
        all_sets = list()
        all_sets.append({1, 2})
        all_sets.append({3, 4})
        all_sets.append({5, 6})
        new_set = {2, 4}
        add_set(all_sets, new_set)
        self.assertEqual(2, len(all_sets))
        self.assertIn({1, 2, 3, 4}, all_sets)
        self.assertIn({5, 6}, all_sets)

    def test_add_one(self):
        all_sets = list()
        all_sets.append({1, 2})
        all_sets.append({3, 4})
        all_sets.append({5, 6})
        new_set = {2, 7}
        add_set(all_sets, new_set)
        self.assertEqual(3, len(all_sets))
        self.assertIn({1, 2, 7}, all_sets)
        self.assertIn({3, 4}, all_sets)
        self.assertIn({5, 6}, all_sets)

    def test_add_new(self):
        all_sets = list()
        all_sets.append({1, 2})
        all_sets.append({3, 4})
        all_sets.append({5, 6})
        new_set = {8, 7}
        add_set(all_sets, new_set)
        self.assertEqual(4, len(all_sets))
        self.assertIn({1, 2}, all_sets)
        self.assertIn({3, 4}, all_sets)
        self.assertIn({5, 6}, all_sets)
        self.assertIn({7, 8}, all_sets)
