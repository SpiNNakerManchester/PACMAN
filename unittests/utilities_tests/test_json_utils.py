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
import unittest
import json
from pacman.config_setup import unittest_setup
from pacman.model.placements import Placement
from pacman.model.resources import (
    ConstantSDRAM, IPtagResource, ReverseIPtagResource)
from pacman.utilities.json_utils import (
    placement_from_json, placement_to_json)
from pacman.model.graphs.machine import SimpleMachineVertex


class TestJsonUtils(unittest.TestCase):
    # ------------------------------------------------------------------
    # Basic graph comparators
    # ------------------------------------------------------------------

    def setUp(self) -> None:
        unittest_setup()

    def _compare_placement(self, p1: Placement, p2: Placement) -> None:
        self.assertEqual(p1.x, p2.x)
        self.assertEqual(p1.y, p2.y)
        self.assertEqual(p1.p, p2.p)
        self.assertEqual(p1.vertex.label, p2.vertex.label)

    # ------------------------------------------------------------------
    # Composite JSON round-trip testing schemes
    # ------------------------------------------------------------------

    def placement_there_and_back(self, there: Placement) -> None:
        j_object = placement_to_json(there)
        j_str = json.dumps(j_object)
        j_object2 = json.loads(j_str)
        back = placement_from_json(j_object2)
        self._compare_placement(there, back)

    # ------------------------------------------------------------------
    # Test cases
    # ------------------------------------------------------------------

    def test_placement(self) -> None:
        s1 = SimpleMachineVertex(
            sdram=ConstantSDRAM(0),
            iptags=[IPtagResource("127.0.0.1", port=456, strip_sdp=True)],
            reverse_iptags=[ReverseIPtagResource(port=25, sdp_port=2, tag=5)],
            label="PVertex")
        p1 = Placement(s1, 1, 2, 3)
        self.placement_there_and_back(p1)
