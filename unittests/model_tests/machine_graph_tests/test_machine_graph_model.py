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
from pacman.model.graphs.application import (
    ApplicationGraph, ApplicationVertex)
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine import (
    MachineEdge, MachineGraph, SimpleMachineVertex)
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanInvalidParameterException)

class AppVertex(ApplicationVertex):
    def __init__(self, label):
        super(AppVertex, self).__init__(label=label)
        self._n_atoms = 3

    @property
    def n_atoms(self):
        return self._n_atoms

    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        pass

    def get_resources_used_by_atoms(self, vertex_slice):
        pass


class TestMachineGraphModel(unittest.TestCase):
    """
    Tests that test the functionality of the machine graph object
    """

    def test_new_vertex(self):
        """
        test the creation of a machine vertex
        """
        SimpleMachineVertex(None, "")

    def test_new_empty_graph(self):
        """
        test that the creation of a empty machine graph works
        """
        MachineGraph("foo")

    def test_new_graph(self):
        """
        tests that after building a machine graph, all partitined vertices
        and partitioned edges are in existence
        """
        vertices = list()
        edges = list()
        for i in range(10):
            vertices.append(SimpleMachineVertex(None, ""))
        for i in range(5):
            edges.append(MachineEdge(vertices[0], vertices[(i + 1)]))
        for i in range(5, 10):
            edges.append(MachineEdge(
                vertices[5], vertices[(i + 1) % 10]))
        graph = MachineGraph("foo")
        graph.add_vertices(vertices)
        graph.add_edges(edges, "bar")
        outgoing = set(graph.get_edges_starting_at_vertex(vertices[0]))
        for i in range(5):
            assert edges[i] in outgoing, \
                "edges[" + str(i) + "] is not in outgoing and should be"
        for i in range(5, 10):
            assert edges[i] not in outgoing, \
                "edges[" + str(i) + "] is in outgoing and shouldn't be"

        incoming = set(graph.get_edges_ending_at_vertex(vertices[0]))

        assert edges[9] in incoming, \
            "edges[9] is not in incoming and should be"
        for i in range(9):
            assert edges[i] not in incoming, \
                "edges[" + str(i) + "] is in incoming and shouldn't be"

        vertices_from_graph = list(graph.vertices)
        for vert in vertices_from_graph:
            self.assertIn(vert, vertices)
        for vert in vertices:
            self.assertEqual(vert, graph.vertex_by_label(vert.label))
        edges_from_graph = list(graph.edges)
        for edge in edges_from_graph:
            self.assertIn(edge, edges)

    def test_add_duplicate_vertex(self):
        """
        testing that adding the same machine vertex twice will cause an
        error
        """
        vertices = list()
        edges = list()
        subv = SimpleMachineVertex(None, "bacon")
        vertices.append(subv)
        vertices.append(SimpleMachineVertex(None, "eggs"))
        vertices.append(subv)
        edges.append(MachineEdge(vertices[0], vertices[1]))
        edges.append(MachineEdge(vertices[1], vertices[0]))
        graph = MachineGraph("foo")
        with self.assertRaises(PacmanAlreadyExistsException):
            graph.add_vertices(vertices)
        graph.add_edges(edges, "bar")

    def test_add_duplicate_edge(self):
        """
        test that adding the same machine edge will cause an error
        """
        vertices = list()
        edges = list()
        vertices.append(SimpleMachineVertex(None, ""))
        vertices.append(SimpleMachineVertex(None, ""))
        edge = MachineEdge(vertices[0], vertices[1])
        edges.append(edge)
        edges.append(edge)
        graph = MachineGraph("foo")
        graph.add_vertices(vertices)
        graph.add_edges(edges, "bar")

    def test_add_edge_with_no_existing_pre_vertex_in_graph(self):
        """
        test that adding a edge where the pre vertex has not been added
        to the machine graph causes an error
        """
        vertices = list()
        edges = list()
        vertices.append(SimpleMachineVertex(None, ""))
        vertices.append(SimpleMachineVertex(None, ""))
        edges.append(MachineEdge(vertices[0], vertices[1]))
        edges.append(MachineEdge(
            SimpleMachineVertex(None, ""), vertices[0]))
        with self.assertRaises(PacmanInvalidParameterException):
            graph = MachineGraph("foo")
            graph.add_vertices(vertices)
            graph.add_edges(edges, "bar")

    def test_add_edge_with_no_existing_post_vertex_in_graph(self):
        """
        test that adding a edge where the post vertex has not been added
        to the machine graph causes an error
        """
        vertices = list()
        edges = list()
        vertices.append(SimpleMachineVertex(None, ""))
        vertices.append(SimpleMachineVertex(None, ""))
        edges.append(MachineEdge(vertices[0], vertices[1]))
        edges.append(MachineEdge(
            vertices[0], SimpleMachineVertex(None, "")))
        with self.assertRaises(PacmanInvalidParameterException):
            graph = MachineGraph("foo")
            graph.add_vertices(vertices)
            graph.add_edges(edges, "bar")

    def test_pre_vertices_by_app_and_partition_name(self):
        app_graph = ApplicationGraph("testA")
        a1 = AppVertex("a1")
        a2 = AppVertex("a2")
        a3 = AppVertex("a3")
        a4 = AppVertex("a4")
        app_graph.add_vertices([a1, a2, a3, a4])
        machine_graph = MachineGraph("testM", app_graph)
        m11 = SimpleMachineVertex(None, "M11", app_vertex=a1)
        m12 = SimpleMachineVertex(None, "M12", app_vertex=a1)
        m21 = SimpleMachineVertex(None, "M21", app_vertex=a2)
        m22 = SimpleMachineVertex(None, "M22", app_vertex=a2)
        m31 = SimpleMachineVertex(None, "M31", app_vertex=a3)
        m41 = SimpleMachineVertex(None, "M41", app_vertex=a4)
        m42 = SimpleMachineVertex(None, "M42", app_vertex=a4)
        m43 = SimpleMachineVertex(None, "M43", app_vertex=a4)
        m44 = SimpleMachineVertex(None, "M44", app_vertex=a4)
        m45 = SimpleMachineVertex(None, "M45", app_vertex=a4)
        m46 = SimpleMachineVertex(None, "M46", app_vertex=a4)
        m47 = SimpleMachineVertex(None, "M47", app_vertex=a4)
        machine_graph.add_vertices(
            [m11, m12, m21, m22, m31, m41, m42, m43, m44, m45, m46, m47])
        machine_graph.add_edge(MachineEdge(m11, m21), "foo")
        machine_graph.add_edge(MachineEdge(m11, m12), "foo")
        machine_graph.add_edge(MachineEdge(m12, m21), "foo")
        machine_graph.add_edge(MachineEdge(m12, m21), "foo")
        machine_graph.add_edge(MachineEdge(m31, m31), "foo")
        machine_graph.add_edge(MachineEdge(m41, m12), "foo")
        machine_graph.add_edge(MachineEdge(m42, m11), "foo")
        machine_graph.add_edge(MachineEdge(m43, m11), "foo")
        machine_graph.add_edge(MachineEdge(m42, m21), "bar")
        machine_graph.add_edge(MachineEdge(m46, m21), "bar")
        machine_graph.add_edge(MachineEdge(m47, m22), "bar")
        machine_graph.add_edge(MachineEdge(m43, m21), "bar")
        machine_graph.add_edge(MachineEdge(
            m43, m31, traffic_type=EdgeTrafficType.SDRAM), "gamma")
        machine_graph.add_edge(MachineEdge(
            m42, m31, traffic_type=EdgeTrafficType.SDRAM), "gamma")
        with self.assertRaises(PacmanInvalidParameterException):
            machine_graph.add_edge(MachineEdge(
                m44, m31, traffic_type=EdgeTrafficType.MULTICAST), "gamma")

        results = machine_graph.multicast_partitions
        # a2 is never a source
        self.assertEquals(3, len(results))
        results1 = results[a1]
        # Only "foo"
        self.assertEquals(1, len(results1))
        vertices = results1["foo"].vertices
        self.assertEquals(set([m11, m12]), vertices)
        self.assertEquals(EdgeTrafficType.MULTICAST,
                          results1["foo"].traffic_type)
        results4 = results[a4]
        # "foo" and "bar
        self.assertEquals(3, len(results4))
        self.assertEquals(set([m41, m42, m43]), results4["foo"].vertices)
        self.assertEquals(set([m42, m43, m46, m47]), results4["bar"].vertices)
        self.assertEquals(set([m42, m43]), results4["gamma"].vertices)
        self.assertEquals(EdgeTrafficType.SDRAM,
                          results4["gamma"].traffic_type)

    def test_add_app_vertex_missing_with_app_level(self):
        app_graph = ApplicationGraph("testA")
        a1 = AppVertex("a1")
        a2 = AppVertex("a2")
        app_graph.add_vertices([a1, a2])
        machine_graph = MachineGraph("testM", app_graph)
        m1 = SimpleMachineVertex(None, "M11")
        m2 = SimpleMachineVertex(None, "M21")
        with self.assertRaises(PacmanInvalidParameterException):
            machine_graph.add_vertices([m1, m2])

    def test_add_app_vertex_missing_no_app_level(self):
        app_graph = ApplicationGraph("testA")
        machine_graph = MachineGraph("testM", app_graph)
        m1 = SimpleMachineVertex(None, "M11")
        m2 = SimpleMachineVertex(None, "M21")
        machine_graph.add_vertices([m1, m2])
        machine_graph.add_edge(MachineEdge(m1, m1), "foo")


if __name__ == '__main__':
    unittest.main()
