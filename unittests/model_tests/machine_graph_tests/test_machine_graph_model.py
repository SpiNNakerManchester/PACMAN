
# pacman imports
from pacman.model.graph.machine.simple_machine_edge import \
    SimpleMachineEdge
from pacman.model.graph.machine.simple_machine_vertex import SimpleMachineVertex
from pacman.model.graph.machine.machine_graph import MachineGraph
from pacman.exceptions import PacmanInvalidParameterException
from pacman.exceptions import PacmanAlreadyExistsException

# general imports
import unittest


class TestMachineGraphModel(unittest.TestCase):
    """
    Tests that test the functionality of the machine graph object
    """

    def test_new_vertex(self):
        """
        test the creation of a machine vertex
        :return:
        """
        SimpleMachineVertex(None, "")

    def test_new_empty_subgraph(self):
        """
        test that the creation of a empty machine graph works
        :return:
        """
        MachineGraph()

    def test_new_subgraph(self):
        """
        tests that after building a machine graph, all partitined vertices
        and partitioend edges are in existance
        :return:
        """
        vertices = list()
        edges = list()
        for i in range(10):
            vertices.append(SimpleMachineVertex(None, ""))
        for i in range(5):
            edges.append(SimpleMachineEdge(vertices[0],
                                                     vertices[(i + 1)]))
        for i in range(5, 10):
            edges.append(SimpleMachineEdge(
                vertices[5], vertices[(i + 1) % 10]))
        subgraph = MachineGraph(vertices=vertices, edges=edges)
        outgoing = subgraph.get_edges_starting_at_vertex(vertices[0])
        for i in range(5):
            if edges[i] not in outgoing:
                raise AssertionError(
                    "edges[" + str(i) + "] is not in outgoing and should be")
        for i in range(5, 10):
            if edges[i] in outgoing:
                raise AssertionError(
                    "edges[" + str(i) + "] is in outgoing and shouldn't be")

        incoming = subgraph.get_edges_ending_at_vertex(vertices[0])

        if edges[9] not in incoming:
            raise AssertionError(
                "edges[9] is not in incoming and should be")
        for i in range(9):
            if edges[i] in incoming:
                raise AssertionError(
                    "edges[" + str(i) + "] is in incoming and shouldn't be")

        vertices_from_subgraph = list(subgraph.vertices)
        for subvert in vertices_from_subgraph:
            self.assertIn(subvert, vertices)
        subvedges_from_subgraph = list(subgraph.edges)
        for subedge in subvedges_from_subgraph:
            self.assertIn(subedge, edges)

    def test_add_duplicate_subvertex(self):
        """
        testing that adding the same machine vertex twice will cause an
        error
        :return:
        """
        vertices = list()
        edges = list()
        subv = SimpleMachineVertex(None, "")
        vertices.append(subv)
        vertices.append(SimpleMachineVertex(None, ""))
        vertices.append(subv)
        edges.append(SimpleMachineEdge(vertices[0],
                                                 vertices[1]))
        edges.append(SimpleMachineEdge(vertices[1],
                                                 vertices[0]))
        with self.assertRaises(PacmanAlreadyExistsException):
            MachineGraph(vertices=vertices, edges=edges)

    def test_add_duplicate_subedge(self):
        """
        test that adding the same machine edge will cause an error
        :return:
        """
        with self.assertRaises(PacmanAlreadyExistsException):
            vertices = list()
            edges = list()
            vertices.append(SimpleMachineVertex(None, ""))
            vertices.append(SimpleMachineVertex(None, ""))
            sube = SimpleMachineEdge(vertices[0], vertices[1])
            edges.append(sube)
            edges.append(sube)
            MachineGraph(vertices=vertices, edges=edges)

    def test_add_edge_with_no_existing_pre_subvertex_in_subgraph(self):
        """
        test that adding a edge where the pre vertex has not been added
        to the machine graph coauses ane rror
        :return:
        """
        vertices = list()
        edges = list()
        vertices.append(SimpleMachineVertex(None, ""))
        vertices.append(SimpleMachineVertex(None, ""))
        edges.append(SimpleMachineEdge(vertices[0],
                                                 vertices[1]))
        edges.append(SimpleMachineEdge(
            SimpleMachineVertex(None, ""), vertices[0]))
        with self.assertRaises(PacmanInvalidParameterException):
            MachineGraph(vertices=vertices, edges=edges)

    def test_add_edge_with_no_existing_post_subvertex_in_subgraph(self):
        """
        test that adding a edge where the post vertex has not been added
        to the machine graph coauses ane rror
        :return:
        """
        vertices = list()
        edges = list()
        vertices.append(SimpleMachineVertex(None, ""))
        vertices.append(SimpleMachineVertex(None, ""))
        edges.append(SimpleMachineEdge(vertices[0],
                                                 vertices[1]))
        edges.append(SimpleMachineEdge(
            vertices[0], SimpleMachineVertex(None, "")))
        with self.assertRaises(PacmanInvalidParameterException):
            MachineGraph(vertices=vertices, edges=edges)


if __name__ == '__main__':
    unittest.main()
