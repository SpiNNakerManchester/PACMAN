# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from testfixtures import LogCapture
from pacman.config_setup import unittest_setup
from pacman.exceptions import PacmanConfigurationException
from pacman.model.partitioner_splitters import SplitterFixedLegacy
from pacman_test_objects import (
    NonLegacyApplicationVertex, SimpleTestVertex)


class TestSplitterFixedLegacy(unittest.TestCase):
    """ Tester for SplitterFixedLegacy
    """

    def setUp(self):
        unittest_setup()

    def test_no_api(self):
        splitter = SplitterFixedLegacy()
        vertex = NonLegacyApplicationVertex()
        with self.assertRaises(PacmanConfigurationException):
            splitter.set_governed_app_vertex(vertex)

    def test_with_api(self):
        splitter = SplitterFixedLegacy()
        vertex = SimpleTestVertex(12)
        with LogCapture() as lc:
            splitter.set_governed_app_vertex(vertex)
            found = False
            for record in lc.records:
                if record.msg.fmt == splitter.NOT_API_WARNING:
                    found = True
            self.assertFalse(found)
