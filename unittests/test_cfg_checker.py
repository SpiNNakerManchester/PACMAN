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

import os
import unittest
from spinn_utilities.config_holder import run_config_checks
from pacman.config_setup import unittest_setup
import pacman
import pacman_test_objects


class TestCfgChecker(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        unittest_setup()

    def test_cfg_check(self) -> None:
        unittests = os.path.dirname(__file__)
        pacman_dir = pacman.__path__[0]
        uinit_test_objects = pacman_test_objects.__path__[0]
        run_config_checks(directories=[
            pacman_dir, unittests, uinit_test_objects])
