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
import json
from pacman.config_setup import unittest_setup
from pacman.model.resources import (
    ConstantSDRAM, IPtagResource, ReverseIPtagResource)
from pacman.utilities.json_utils import (vertex_to_json, vertex_from_json)
from pacman.model.graphs.machine import SimpleMachineVertex


class TestJsonUtils(unittest.TestCase):
    # ------------------------------------------------------------------
    # Basic graph comparators
    # ------------------------------------------------------------------

    def setUp(self):
        unittest_setup()

    def _compare_constraint(self, c1, c2, seen=None):
        if seen is None:
            seen = []
        if c1 == c2:
            return
        if c1.__class__ != c2.__class__:
            raise AssertionError("{} != {}".format(
                c1.__class__, c2.__class__))
        self._compare_vertex(c1.vertex, c2.vertex, seen)

    def _compare_vertex(self, v1, v2, seen=None):
        if seen is None:
            seen = []
        self.assertEqual(v1.label, v2.label)
        if v1.label in seen:
            return
        self.assertEqual(v1.sdram_required, v2.sdram_required)
        seen.append(v1.label)

    # ------------------------------------------------------------------
    # Composite JSON round-trip testing schemes
    # ------------------------------------------------------------------

    def vertex_there_and_back(self, there):
        j_object = vertex_to_json(there)
        j_str = json.dumps(j_object)
        j_object2 = json.loads(j_str)
        back = vertex_from_json(j_object2)
        self._compare_vertex(there, back)

    # ------------------------------------------------------------------
    # Test cases
    # ------------------------------------------------------------------

    def test_vertex(self):
        s1 = SimpleMachineVertex(
            sdram=ConstantSDRAM(0),
            iptags=[IPtagResource("127.0.0.1", port=None, strip_sdp=True)],
            reverse_iptags=[ReverseIPtagResource(port=25, sdp_port=2, tag=5)],
            label="Vertex")
        self.vertex_there_and_back(s1)
