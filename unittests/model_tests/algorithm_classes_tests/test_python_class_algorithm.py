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
from pacman.executor.algorithm_classes import PythonClassAlgorithm


class TestPythonClassAlgorithm(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def setUp(self):
        unittest_setup()

    def test_python_class(self):
        python_module = "Foo"
        python_class = "Bar"
        alg = PythonClassAlgorithm("algorithm_id", [], [], [], [], [], [],
                                   python_module, python_class)
        self.assertEqual(python_module, alg._python_module)
        self.assertEqual(python_class, alg._python_class)
        self.assertIsNone(alg._python_method)

    def test_python_method(self):
        python_module = "Foo"
        python_class = "Bar"
        python_method = "grill"
        alg = PythonClassAlgorithm("algorithm_id", [], [], [], [], [], [],
                                   python_module, python_class, python_method)
        self.assertEqual(python_module, alg._python_module)
        self.assertEqual(python_class, alg._python_class)
        self.assertEqual(python_method, alg._python_method)
