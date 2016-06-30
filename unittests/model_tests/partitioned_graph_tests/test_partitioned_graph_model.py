"""
TestPartitionedGraphModel
"""

# pacman imports
from pacman.model.partitioned_graph.multi_cast_partitioned_edge import \
    MultiCastPartitionedEdge
from pacman.model.graph.simple_partitioned_vertex import SimplePartitionedVertex
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.exceptions import PacmanInvalidParameterException
from pacman.exceptions import PacmanAlreadyExistsException

# general imports
import unittest


class TestPartitionedGraphModel(unittest.TestCase):
    """
    Tests that test the functionality of the partitioned graph object
    """

    def test_new_vertex(self):
        """
        test the creation of a partitioned vertex
        :return:
        """
        SimplePartitionedVertex(None, "")

    def test_new_empty_subgraph(self):
        """
        test that the creation of a empty partitioned graph works
        :return:
        """
        PartitionedGraph()

    def test_new_subgraph(self):
        """
        tests that after building a partitioned graph, all partitined vertices
        and partitioend edges are in existance
        :return:
        """
        subvertices = list()
        subedges = list()
        for i in range(10):
            subvertices.append(SimplePartitionedVertex(None, ""))
        for i in range(5):
            subedges.append(MultiCastPartitionedEdge(subvertices[0],
                                                     subvertices[(i + 1)]))
        for i in range(5, 10):
            subedges.append(MultiCastPartitionedEdge(
                subvertices[5], subvertices[(i + 1) % 10]))
        subgraph = PartitionedGraph(subvertices=subvertices, subedges=subedges)
        outgoing = subgraph.outgoing_subedges_from_subvertex(subvertices[0])
        for i in range(5):
            if subedges[i] not in outgoing:
                raise AssertionError(
                    "subedges[" + str(i) + "] is not in outgoing and should be")
        for i in range(5, 10):
            if subedges[i] in outgoing:
                raise AssertionError(
                    "subedges[" + str(i) + "] is in outgoing and shouldn't be")

        incoming = subgraph.incoming_subedges_from_subvertex(subvertices[0])

        if subedges[9] not in incoming:
            raise AssertionError(
                "subedges[9] is not in incoming and should be")
        for i in range(9):
            if subedges[i] in incoming:
                raise AssertionError(
                    "subedges[" + str(i) + "] is in incoming and shouldn't be")

        subvertices_from_subgraph = list(subgraph.subvertices)
        for subvert in subvertices_from_subgraph:
            self.assertIn(subvert, subvertices)
        subvedges_from_subgraph = list(subgraph.subedges)
        for subedge in subvedges_from_subgraph:
            self.assertIn(subedge, subedges)

    def test_add_duplicate_subvertex(self):
        """
        testing that adding the same partitioned vertex twice will cause an
        error
        :return:
        """
        subvertices = list()
        subedges = list()
        subv = SimplePartitionedVertex(None, "")
        subvertices.append(subv)
        subvertices.append(SimplePartitionedVertex(None, ""))
        subvertices.append(subv)
        subedges.append(MultiCastPartitionedEdge(subvertices[0],
                                                 subvertices[1]))
        subedges.append(MultiCastPartitionedEdge(subvertices[1],
                                                 subvertices[0]))
        with self.assertRaises(PacmanAlreadyExistsException):
            PartitionedGraph(subvertices=subvertices, subedges=subedges)

    def test_add_duplicate_subedge(self):
        """
        test that adding the same partitioned edge will cause an error
        :return:
        """
        with self.assertRaises(PacmanAlreadyExistsException):
            subvertices = list()
            subedges = list()
            subvertices.append(SimplePartitionedVertex(None, ""))
            subvertices.append(SimplePartitionedVertex(None, ""))
            sube = MultiCastPartitionedEdge(subvertices[0], subvertices[1])
            subedges.append(sube)
            subedges.append(sube)
            PartitionedGraph(subvertices=subvertices, subedges=subedges)

    def test_add_subedge_with_no_existing_pre_subvertex_in_subgraph(self):
        """
        test that adding a edge where the pre vertex has not been added
        to the partitioned graph coauses ane rror
        :return:
        """
        subvertices = list()
        subedges = list()
        subvertices.append(SimplePartitionedVertex(None, ""))
        subvertices.append(SimplePartitionedVertex(None, ""))
        subedges.append(MultiCastPartitionedEdge(subvertices[0],
                                                 subvertices[1]))
        subedges.append(MultiCastPartitionedEdge(
            SimplePartitionedVertex(None, ""), subvertices[0]))
        with self.assertRaises(PacmanInvalidParameterException):
            PartitionedGraph(subvertices=subvertices, subedges=subedges)

    def test_add_subedge_with_no_existing_post_subvertex_in_subgraph(self):
        """
        test that adding a edge where the post vertex has not been added
        to the partitioned graph coauses ane rror
        :return:
        """
        subvertices = list()
        subedges = list()
        subvertices.append(SimplePartitionedVertex(None, ""))
        subvertices.append(SimplePartitionedVertex(None, ""))
        subedges.append(MultiCastPartitionedEdge(subvertices[0],
                                                 subvertices[1]))
        subedges.append(MultiCastPartitionedEdge(
            subvertices[0], SimplePartitionedVertex(None, "")))
        with self.assertRaises(PacmanInvalidParameterException):
            PartitionedGraph(subvertices=subvertices, subedges=subedges)


if __name__ == '__main__':
    unittest.main()
