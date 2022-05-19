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
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint, FixedKeyAndMaskConstraint,
    FixedMaskConstraint)
from pacman.model.constraints.placer_constraints import (
    BoardConstraint, ChipAndCoreConstraint, RadialPlacementFromChipConstraint,
    SameChipAsConstraint)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, SameAtomsAsVertexConstraint)
from pacman.model.graphs.machine import MulticastEdgePartition
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, IPtagResource,
    ResourceContainer)
from pacman.model.routing_info import BaseKeyAndMask
from pacman.utilities import file_format_schemas
from pacman.utilities.json_utils import (
    constraint_to_json, constraint_from_json,
    edge_to_json, edge_from_json,
    graph_to_json, graph_from_json,
    resource_container_to_json, resource_container_from_json,
    vertex_to_json, vertex_from_json)
from pacman.model.graphs.machine import (
    MachineEdge, MachineGraph, SimpleMachineVertex)

MACHINE_GRAPH_FILENAME = "machine_graph.json"


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
        self.assertEqual(v1.resources_required, v2.resources_required)
        self.assertEqual(len(v1.constraints), len(v2.constraints))
        seen.append(v1.label)
        for c1, c2 in zip(self.__constraints(v1), self.__constraints(v2)):
            self._compare_constraint(c1, c2, seen)

    # ------------------------------------------------------------------
    # Composite JSON round-trip testing schemes
    # ------------------------------------------------------------------

    def constraint_there_and_back(self, there):
        j_object = constraint_to_json(there)
        j_str = json.dumps(j_object)
        j_object2 = json.loads(j_str)
        back = constraint_from_json(j_object2)
        self._compare_constraint(there, back)

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

    def edge_there_and_back(self, there):
        j_object = edge_to_json(there)
        j_str = json.dumps(j_object)
        j_object2 = json.loads(j_str)
        back = edge_from_json(j_object2)
        self.assertEqual(there.label, back.label)
        self._compare_vertex(there.pre_vertex, back.pre_vertex)
        self._compare_vertex(there.post_vertex, back.post_vertex)
        self.assertEqual(there.traffic_type, back.traffic_type)
        self.assertEqual(there.traffic_weight, back.traffic_weight)

    def graph_there_and_back(self, there):
        j_object = graph_to_json(there)
        print(j_object)
        file_format_schemas.validate(j_object, MACHINE_GRAPH_FILENAME)
        back = graph_from_json(j_object)
        self.assertEqual(there.n_vertices, back.n_vertices)
        for vertex in there.vertices:
            b_vertex = back.vertex_by_label(vertex.label)
            self._compare_vertex(vertex, b_vertex)

    # ------------------------------------------------------------------
    # Test cases
    # ------------------------------------------------------------------

    def test_board_constraint(self):
        c1 = BoardConstraint("1.2.3.4")
        self.constraint_there_and_back(c1)

    def test_chip_and_core_constraint(self):
        c1 = ChipAndCoreConstraint(1, 2)
        self.constraint_there_and_back(c1)
        c2 = ChipAndCoreConstraint(1, 2, 3)
        self.constraint_there_and_back(c2)

    def test_radial_placement_from_chip_constraint(self):
        c1 = RadialPlacementFromChipConstraint(1, 2)
        self.constraint_there_and_back(c1)

    def test_same_chip_as_constraint(self):
        v1 = SimpleMachineVertex(None, "v1")
        c1 = SameChipAsConstraint(v1)
        self.constraint_there_and_back(c1)

    def test_same_atoms_as_vertex_constraint(self):
        with self.assertRaises(NotImplementedError):
            v1 = SimpleMachineVertex(None, "v1")
            c1 = SameAtomsAsVertexConstraint(v1)
            self.constraint_there_and_back(c1)

    def test_max_vertex_atoms_constraint(self):
        c1 = MaxVertexAtomsConstraint(5)
        self.constraint_there_and_back(c1)

    def test_contiguous_key_range_constraint(self):
        c1 = ContiguousKeyRangeContraint()
        self.constraint_there_and_back(c1)

    def test_fixed_key_and_mask_constraint(self):
        c1 = FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0xFF0, 0xFF8)])
        self.constraint_there_and_back(c1)
        km = BaseKeyAndMask(0xFF0, 0xFF8)
        km2 = BaseKeyAndMask(0xFE0, 0xFF8)
        c2 = FixedKeyAndMaskConstraint([km, km2])
        self.constraint_there_and_back(c2)

    def test_fixed_mask_constraint(self):
        c1 = FixedMaskConstraint(0xFF0)
        self.constraint_there_and_back(c1)

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
        s1 = SimpleMachineVertex(ResourceContainer(iptags=[IPtagResource(
            "127.0.0.1", port=None, strip_sdp=True)]),
            label="Vertex")
        self.vertex_there_and_back(s1)

    def test_vertex2(self):
        """Like test_vertex, but with constraints."""
        c1 = ContiguousKeyRangeContraint()
        c2 = BoardConstraint("1.2.3.4")
        s1 = SimpleMachineVertex(ResourceContainer(iptags=[IPtagResource(
            "127.0.0.1", port=None, strip_sdp=True)]),
            label="Vertex", constraints=[c1, c2])
        self.vertex_there_and_back(s1)

    def test_same_chip_as_constraint_plus(self):
        v1 = SimpleMachineVertex(None, "v1")
        c1 = SameChipAsConstraint(v1)
        self.constraint_there_and_back(c1)

    def test_edge(self):
        v1 = SimpleMachineVertex(None, "One")
        v2 = SimpleMachineVertex(None, "Two")
        e1 = MachineEdge(v1, v2)
        self.edge_there_and_back(e1)

    def test_new_empty_graph(self):
        """
        test that the creation of a empty machine graph works
        """
        m1 = MachineGraph("foo")
        self.graph_there_and_back(m1)

    def test_new_graph(self):
        """
        tests that after building a machine graph, all partitined vertices
        and partitioned edges are in existence
        """
        vertices = list()
        edges = list()
        for i in range(10):
            vertices.append(
                SimpleMachineVertex(ResourceContainer(), "V{}".format(i)))
        with self.assertRaises(NotImplementedError):
            vertices[1].add_constraint(SameAtomsAsVertexConstraint(
                vertices[4]))
            vertices[4].add_constraint(SameAtomsAsVertexConstraint(
                vertices[1]))
        for i in range(5):
            edges.append(MachineEdge(vertices[0], vertices[(i + 1)]))
        for i in range(5, 10):
            edges.append(MachineEdge(
                vertices[5], vertices[(i + 1) % 10]))
        graph = MachineGraph("foo")
        graph.add_vertices(vertices)
        graph.add_outgoing_edge_partition(MulticastEdgePartition(
            identifier="bar", pre_vertex=vertices[0]))
        graph.add_outgoing_edge_partition(MulticastEdgePartition(
            identifier="bar", pre_vertex=vertices[5]))
        graph.add_edges(edges, "bar")
        self.graph_there_and_back(graph)
