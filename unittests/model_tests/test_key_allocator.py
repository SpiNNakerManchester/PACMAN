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
from pacman.exceptions import PacmanConfigurationException
from pacman.model.routing_info import BaseKeyAndMask
from pacman.model.constraints import FixedKeyAndMaskConstraint


class TestKeyAllocatorConstraints(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_fixed_key_and_mask_constraint(self):
        c1 = FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0xFF0, 0xFF8)])
        km = BaseKeyAndMask(0xFF0, 0xFF8)
        c2 = FixedKeyAndMaskConstraint([km])
        c3 = FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0xFE0, 0xFF8)])
        c4 = FixedKeyAndMaskConstraint([
            km, BaseKeyAndMask(0xFE0, 0xFF8)])
        self.assertEqual(c1, c2)
        self.assertEqual(c1.keys_and_masks, [km])
        r = ("FixedKeyAndMaskConstraint(keys_and_masks=[KeyAndMask:0xff0:"
             "0xff8], partition=None)")
        self.assertEqual(str(c1), r)
        d = {}
        d[c1] = 1
        d[c2] = 2
        d[c3] = 3
        self.assertEqual(len(d), 2)
        self.assertEqual(d[c1], 2)
        self.assertNotEqual(c4, c1)
        self.assertNotEqual(c1, c4)

    def test_partition(self):
        km = BaseKeyAndMask(0xFF0, 0xFF8)
        c1 = FixedKeyAndMaskConstraint([km])
        self.assertIsNone(c1.partition)
        c2 = FixedKeyAndMaskConstraint([km], "spikes")
        self.assertEqual(c2.partition, "spikes")
        self.assertNotEqual(c1, km)
        self.assertNotEqual(km, c1)

    def test_safety_code(self):
        with self.assertRaises(PacmanConfigurationException):
            FixedKeyAndMaskConstraint([BaseKeyAndMask(0xFE0, 0xFF8), "bacon"])
