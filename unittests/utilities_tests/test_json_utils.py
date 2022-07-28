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
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, IPtagResource,
    ResourceContainer)
from pacman.utilities.json_utils import (
    resource_container_to_json, resource_container_from_json,
    vertex_to_json, vertex_from_json)
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

    @staticmethod
    def __constraints(vertex):
        return sorted(vertex.constraints, key=lambda c: c.__class__.__name__)

    def _compare_vertex(self, v1, v2, seen=None):
        if seen is None:
            seen = []
        self.assertEqual(v1.label, v2.label)
        if v1.label in seen:
            return
        self.assertEqual(v1.sdram_required, v2.sdram_required)
        self.assertEqual(len(v1.constraints), len(v2.constraints))
        seen.append(v1.label)
        for c1, c2 in zip(self.__constraints(v1), self.__constraints(v2)):
            self._compare_constraint(c1, c2, seen)

    # ------------------------------------------------------------------
    # Composite JSON round-trip testing schemes
    # ------------------------------------------------------------------

    def resource_there_and_back(self, there):
        j_object = resource_container_to_json(there)
        j_str = json.dumps(j_object)
        j_object2 = json.loads(j_str)
        back = resource_container_from_json(j_object2)
        self.assertEqual(there, back)

    def vertex_there_and_back(self, there):
        j_object = vertex_to_json(there)
        j_str = json.dumps(j_object)
        j_object2 = json.loads(j_str)
        back = vertex_from_json(j_object2)
        self._compare_vertex(there, back)

    # ------------------------------------------------------------------
    # Test cases
    # ------------------------------------------------------------------

    def test_tags_resources(self):
        t1 = IPtagResource("1", 2, True)  # Minimal args
        r1 = ResourceContainer(iptags=[t1])
        self.resource_there_and_back(r1)
        t2 = IPtagResource("1.2.3.4", 2, False, 4, 5)
        r2 = ResourceContainer(reverse_iptags=[t2])
        self.resource_there_and_back(r2)

    def test_resource_container(self):
        sdram1 = ConstantSDRAM(128 * (2**20))
        dtcm = DTCMResource(128 * (2**20) + 1)
        cpu = CPUCyclesPerTickResource(128 * (2**20) + 2)
        r1 = ResourceContainer(dtcm, sdram1, cpu)
        self.resource_there_and_back(r1)
        t1 = IPtagResource("1", 2, True)  # Minimal args
        t2 = IPtagResource("1.2.3.4", 2, False, 4, 5)
        r2 = r1 = ResourceContainer(dtcm, sdram1, cpu, iptags=[t1, t2])
        self.resource_there_and_back(r2)

    def test_vertex(self):
        s1 = SimpleMachineVertex(
            sdram=ConstantSDRAM(0),
            iptags=[IPtagResource("127.0.0.1", port=None, strip_sdp=True)],
            label="Vertex")
        self.vertex_there_and_back(s1)
