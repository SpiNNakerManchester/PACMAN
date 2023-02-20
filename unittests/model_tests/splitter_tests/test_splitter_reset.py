# Copyright (c) 2022 The University of Manchester
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
from pacman.config_setup import unittest_setup
from pacman.data import PacmanDataView
from pacman.model.partitioner_splitters import (
    SplitterFixedLegacy, splitter_reset)
from pacman_test_objects import SimpleTestVertex


class TestSplitterReset(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_reset(self):
        # With slitter
        v1 = SimpleTestVertex(1, "v1")
        PacmanDataView.add_vertex(v1)
        splitter = SplitterFixedLegacy()
        v1.splitter = splitter
        # no splitter
        v2 = SimpleTestVertex(1, "v2")
        PacmanDataView.add_vertex(v2)
        splitter_reset.splitter_reset()
