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
from pacman.executor.algorithm_classes import PythonFunctionAlgorithm


class TestPythonFunctionAlgorithm(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def test_python_module(self):
        python_module = "Foo"
        python_function = "bar"
        alg = PythonFunctionAlgorithm("algorithm_id", [], [], [], [], [], [],
                                      python_module, python_function)
        self.assertEqual(python_module, alg._python_module)
        self.assertEqual(python_function, alg._python_function)
