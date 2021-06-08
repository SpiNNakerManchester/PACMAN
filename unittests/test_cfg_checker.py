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

import os
import unittest
from spinn_utilities.config_holder import run_config_checks
from pacman.config_setup import reset_configs


class TestCfgChecker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        reset_configs()

    def test_cfg_check(self):
        unittests = os.path.dirname(__file__)
        parent = os.path.dirname(unittests)
        pacman = os.path.join(parent, "pacman")
        integration_tests = os.path.join(parent, "pacman_integration_tests")
        uinit_test_objects = os.path.join(parent, "pacman_test_objects")
        run_config_checks(directories=[
            pacman, integration_tests, unittests, uinit_test_objects])
