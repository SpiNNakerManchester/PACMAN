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
from pacman.model.graphs.application import ApplicationGraph
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine import (
    ConstantSDRAMMachinePartition, MachineEdge, MachineGraph,
    MulticastEdgePartition, SDRAMMachineEdge, SimpleMachineVertex)
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanConfigurationException,
    PacmanInvalidParameterException)
from uinit_test_objects import SimpleTestVertex


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
        graph.add_outgoing_edge_partition(
            MulticastEdgePartition(vertices[0], "bar"))
        graph.add_outgoing_edge_partition(
            MulticastEdgePartition(vertices[5], "bar"))
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

        second = graph.clone(False)
        self.assertEqual(graph.n_vertices, second.n_vertices)
        vertices_from_graph = list(second.vertices)
        for vert in vertices_from_graph:
            self.assertIn(vert, vertices)
        for vert in vertices:
            self.assertEqual(vert, graph.vertex_by_label(vert.label))
        self.assertEqual(graph.n_outgoing_edge_partitions,
                         second.n_outgoing_edge_partitions)
        edges_from_graph = list(second.edges)
        for edge in edges_from_graph:
            self.assertIn(edge, edges)
        self.assertEqual(len(edges_from_graph), len(edges))

        third = graph.clone(True)
        self.assertEqual(graph.n_vertices, third.n_vertices)
        vertices_from_graph = list(third.vertices)
        for vert in vertices_from_graph:
            self.assertIn(vert, vertices)
        for vert in vertices:
            self.assertEqual(vert, graph.vertex_by_label(vert.label))
        self.assertEqual(graph.n_outgoing_edge_partitions,
                         third.n_outgoing_edge_partitions)
        edges_from_graph = list(third.edges)
        for edge in edges_from_graph:
            self.assertIn(edge, edges)
        self.assertEqual(len(edges_from_graph), len(edges))
        with self.assertRaises(PacmanConfigurationException):
            third.add_edge("mock", "mock")
        with self.assertRaises(PacmanConfigurationException):
            third.add_vertex("mock")
        with self.assertRaises(PacmanConfigurationException):
            third.add_outgoing_edge_partition("mock")

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
        graph.add_outgoing_edge_partition(
            MulticastEdgePartition(vertices[0], "bar"))
        graph.add_outgoing_edge_partition(
            MulticastEdgePartition(vertices[1], "bar"))
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
        graph.add_outgoing_edge_partition(
            MulticastEdgePartition(vertices[0], "bar"))
        with self.assertRaises(PacmanAlreadyExistsException):
            graph.add_edges(edges, "bar")

    def test_all_have_app_vertex(self):
        app_graph = ApplicationGraph("Test")
        graph = MachineGraph("foo", app_graph)
        app1 = SimpleTestVertex(12, "app1")
        mach1 = SimpleMachineVertex("mach1",  app_vertex=app1)
        mach2 = SimpleMachineVertex("mach2",  app_vertex=app1)
        mach3 = SimpleMachineVertex("mach3",  app_vertex=None)
        graph.add_vertices([mach1, mach2])
        with self.assertRaises(PacmanInvalidParameterException):
            graph.add_vertex(mach3)

    def test_none_have_app_vertex(self):
        app_graph = ApplicationGraph("Test")
        graph = MachineGraph("foo", app_graph)
        app1 = SimpleTestVertex(12, "app1")
        mach1 = SimpleMachineVertex("mach1",  app_vertex=None)
        mach2 = SimpleMachineVertex("mach2",  app_vertex=None)
        mach3 = SimpleMachineVertex("mach3",  app_vertex=app1)
        graph.add_vertices([mach1, mach2])
        with self.assertRaises(PacmanInvalidParameterException):
            graph.add_vertex(mach3)

    def test_no_app_graph_no_app_vertex(self):
        graph = MachineGraph("foo")
        app1 = SimpleTestVertex(12, "app1")
        mach1 = SimpleMachineVertex("mach1", app_vertex=app1)
        mach2 = SimpleMachineVertex("mach2", app_vertex=None)
        mach3 = SimpleMachineVertex("mach3", app_vertex=app1)
        with self.assertRaises(PacmanInvalidParameterException):
            graph.add_vertex(mach1)
        graph.add_vertex(mach2)
        with self.assertRaises(PacmanInvalidParameterException):
            graph.add_vertex(mach3)

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
        vertex_extra = SimpleMachineVertex(None, "")
        edges.append(MachineEdge(vertex_extra, vertices[0]))
        with self.assertRaises(PacmanInvalidParameterException):
            graph = MachineGraph("foo")
            graph.add_vertices(vertices)
            graph.add_outgoing_edge_partition(
                MulticastEdgePartition(vertices[0], "ba"))
            graph.add_outgoing_edge_partition(
                MulticastEdgePartition(vertex_extra, "bar"))
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
        edges.append(MachineEdge(vertices[0], SimpleMachineVertex(None, "")))
        with self.assertRaises(PacmanInvalidParameterException):
            graph = MachineGraph("foo")
            graph.add_vertices(vertices)
            graph.add_outgoing_edge_partition(
                MulticastEdgePartition(vertices[0], "bar"))
            graph.add_edges(edges, "bar")

    def test_remember_machine_vertex(self):
        app_graph = ApplicationGraph("Test")
        graph = MachineGraph("foo", app_graph)
        app1 = SimpleTestVertex(12, "app1")
        app2 = SimpleTestVertex(12, "app2")
        mach1 = SimpleMachineVertex("mach1",  app_vertex=app1)
        mach2 = SimpleMachineVertex("mach2",  app_vertex=app1)
        mach3 = SimpleMachineVertex("mach3",  app_vertex=app1)
        mach4 = SimpleMachineVertex("mach4",  app_vertex=app2)
        self.assertEquals(0, len(app1.machine_vertices))
        self.assertEquals(0, len(app2.machine_vertices))
        graph.add_vertices([mach1, mach2])
        graph.add_vertex(mach3)
        graph.add_vertex(mach4)
        self.assertEquals(3, len(app1.machine_vertices))
        self.assertEquals(1, len(app2.machine_vertices))
        self.assertIn(mach1, app1.machine_vertices)
        self.assertIn(mach2, app1.machine_vertices)
        self.assertIn(mach3, app1.machine_vertices)
        self.assertIn(mach4, app2.machine_vertices)

    def test_at_vertex_methods(self):
        graph = MachineGraph("foo")
        mach1 = SimpleMachineVertex("mach1")
        mach2 = SimpleMachineVertex("mach2")
        mach3 = SimpleMachineVertex("mach3")
        mach4 = SimpleMachineVertex("mach4")
        graph.add_vertices([mach1, mach2, mach3, mach4])

        # Add partition then edge
        part_m_1 = MulticastEdgePartition(mach1, "spikes")
        graph.add_outgoing_edge_partition(part_m_1)
        edge_m_11 = MachineEdge(
            mach1, mach2, traffic_type=EdgeTrafficType.MULTICAST)
        graph.add_edge(edge_m_11, "spikes")
        # check clear error it you add the edge again
        with self.assertRaises(PacmanAlreadyExistsException):
            graph.add_edge(edge_m_11, "spikes")
        self.assertIn(edge_m_11, part_m_1.edges)
        edge_m_12 = MachineEdge(
            mach1, mach3, traffic_type=EdgeTrafficType.MULTICAST)
        graph.add_edge(edge_m_12, "spikes")
        edge_m_21 = MachineEdge(
            mach3, mach4, traffic_type=EdgeTrafficType.MULTICAST)
        graph.add_edge(edge_m_21, "spikes")
        part_m_2 = graph.get_outgoing_partition_for_edge(edge_m_21)

        edge_f_1 = MachineEdge(
            mach1, mach3, traffic_type=EdgeTrafficType.FIXED_ROUTE)
        graph.add_edge(edge_f_1, "Control")
        part_f = graph.get_outgoing_partition_for_edge(edge_f_1)

        part_s_1 = ConstantSDRAMMachinePartition("ram", mach1, "ram1")
        graph.add_outgoing_edge_partition(part_s_1)
        edge_s_11 = SDRAMMachineEdge(mach1, mach2, "s1")
        graph.add_edge(edge_s_11, "ram")
        edge_s_12 = SDRAMMachineEdge(mach1, mach3, "s2")
        graph.add_edge(edge_s_12, "ram")

        starting_at_mach1 = list(
            graph.get_outgoing_edge_partitions_starting_at_vertex(mach1))
        self.assertIn(part_m_1, starting_at_mach1)
        self.assertIn(part_f, starting_at_mach1)
        self.assertIn(part_s_1, starting_at_mach1)
        self.assertEqual(3, len(starting_at_mach1))

        starting_at_mach3 = list(
            graph.get_outgoing_edge_partitions_starting_at_vertex(mach3))
        self.assertIn(part_m_2, starting_at_mach3)
        self.assertEqual(1, len(starting_at_mach3))

        starting_at_mach4 = list(
            graph.get_outgoing_edge_partitions_starting_at_vertex(mach4))
        self.assertEqual(0, len(starting_at_mach4))

        ending_at_mach2 = list(
            graph.get_edge_partitions_ending_at_vertex(mach2))
        self.assertIn(part_m_1, ending_at_mach2)
        self.assertIn(part_s_1, ending_at_mach2)
        self.assertEqual(2, len(ending_at_mach2))

        ending_at_mach3 = list(
            graph.get_edge_partitions_ending_at_vertex(mach3))
        self.assertIn(part_m_1, ending_at_mach3)
        self.assertIn(part_f, ending_at_mach3)
        self.assertIn(part_s_1, ending_at_mach3)
        self.assertEqual(3, len(ending_at_mach3))

        ending_at_mach1 = list(
            graph.get_edge_partitions_ending_at_vertex(mach1))
        self.assertEqual(0, len(ending_at_mach1))


if __name__ == '__main__':
    unittest.main()
