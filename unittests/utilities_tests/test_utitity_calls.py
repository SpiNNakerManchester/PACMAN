# Copyright (c) 2026 The University of Manchester
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
from pacman.exceptions import PacmanValueError
from pacman.utilities.utility_calls import (
    calc_shift, can_shift, signifacant_zone)


class TestItilityCalls(unittest.TestCase):

    def test_calc_shift(self) -> None:
        self.assertEqual(8, calc_shift(0xFFFFFF00))
        self.assertEqual(30, calc_shift(0xc0000000))

        # mask in the middle does not shift
        with self.assertRaises(PacmanValueError):
            self.assertEqual(8, calc_shift(0xFFFF00FF))

        self.assertEqual(1, calc_shift(0xFFFFFFFe))

        # All masked has shiuft zero
        self.assertEqual(0, calc_shift(0xFFFFFFFF))

        # weird but all unmasked is a full shift
        self.assertEqual(32, calc_shift(0x0))

    def test_can_shift(self) -> None:
        self.assertTrue(can_shift(0xFFFFFF00))
        self.assertTrue(can_shift(0xc0000000))

        # mask in the middle does not shift
        self.assertFalse(can_shift(0xFFFF00FF))

        # All masked can shift
        self.assertTrue(can_shift(0xFFFFFFFF))

        # weird but all unmasked is a full shift
        self.assertTrue(can_shift(0x0))

    def test_signifacant_zone(self) -> None:
        self.assertEqual((0, 3), signifacant_zone(0xF0000000))
        self.assertEqual((11, 11), signifacant_zone(0x00100000))
        self.assertEqual((10, 18), signifacant_zone(0x00302000))
        self.assertEqual((28, 31), signifacant_zone(0x0000000F))
        self.assertEqual((3, 7), signifacant_zone(0x11000000))
        self.assertEqual((18, 18), signifacant_zone(0x00002000))
        self.assertIsNone(signifacant_zone(0x00000000))
        self.assertFalse(0x00000000)
