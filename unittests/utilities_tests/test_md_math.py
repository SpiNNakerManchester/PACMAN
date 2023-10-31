# Copyright (c) 2023 The University of Manchester
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
from pacman.utilities.md_math import check_md_math


class TestMD_Math(unittest.TestCase):

    def test_singelton(self):
        check_md_math(neurons_per_cores=[1], cores_per_size=[1])

    def test_1d(self):
        check_md_math(neurons_per_cores=[3], cores_per_size=[5])

    def test_2d(self):
        check_md_math(neurons_per_cores=[3, 3], cores_per_size=[2, 2])

    def test_3d(self):
        check_md_math(neurons_per_cores=[2, 3, 4], cores_per_size=[4, 5, 3])


if __name__ == '__main__':
    unittest.main()
