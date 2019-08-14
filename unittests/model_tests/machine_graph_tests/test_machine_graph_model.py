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
from pacman.model.graphs.machine import (
    MachineEdge, MachineGraph, SimpleMachineVertex)
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanInvalidParameterException)


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
        subv = SimpleMachineVertex(None, "")
        vertices.append(subv)
        vertices.append(SimpleMachineVertex(None, ""))
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


if __name__ == '__main__':
    unittest.main()
