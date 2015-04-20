"""
TestPartitionedGraphModel
"""

# pacman imports
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.model.partitioned_graph.abstract_partitioned_edge\
    import AbstractPartitionedEdge
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
        PartitionedVertex(None, "")

    def test_new_empty_subgraph(self):
        """
        test that the creation of a
        :return:
        """
        PartitionedGraph()

    def test_new_subgraph(self):
        subvertices = list()
        subedges = list()
        for i in range(10):
            subvertices.append(PartitionedVertex(0, 4, None))
        for i in range(5):
            subedges.append(AbstractPartitionedEdge(subvertices[0], subvertices[(i + 1)]))
        for i in range(5, 10):
            subedges.append(AbstractPartitionedEdge(subvertices[5], subvertices[(i + 1) % 10]))
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
        subvertices = list()
        subedges = list()
        subv = PartitionedVertex(0, 4, None)
        subvertices.append(subv)
        subvertices.append(PartitionedVertex(5, 9, None))
        subvertices.append(subv)
        subedges.append(AbstractPartitionedEdge(subvertices[0], subvertices[1]))
        subedges.append(AbstractPartitionedEdge(subvertices[1], subvertices[0]))
        with self.assertRaises(PacmanAlreadyExistsException):
            PartitionedGraph(subvertices=subvertices, subedges=subedges)

    def test_add_duplicate_subedge(self):
        with self.assertRaises(PacmanAlreadyExistsException):
            subvertices = list()
            subedges = list()
            subvertices.append(PartitionedVertex(5, 9, None))
            subvertices.append(PartitionedVertex(5, 9, None))
            sube = AbstractPartitionedEdge(subvertices[0], subvertices[1])
            subedges.append(sube)
            subedges.append(sube)
            PartitionedGraph(subvertices=subvertices, subedges=subedges)

    def test_add_subedge_with_no_existing_pre_subvertex_in_subgraph(self):
        subvertices = list()
        subedges = list()
        subvertices.append(PartitionedVertex(0, 4, None))
        subvertices.append(PartitionedVertex(5, 9, None))
        subedges.append(AbstractPartitionedEdge(subvertices[0], subvertices[1]))
        subedges.append(AbstractPartitionedEdge(PartitionedVertex(0, 100, None), subvertices[0]))
        with self.assertRaises(PacmanInvalidParameterException):
            PartitionedGraph(subvertices=subvertices, subedges=subedges)

    def test_add_subedge_with_no_existing_post_subvertex_in_subgraph(self):
        subvertices = list()
        subedges = list()
        subvertices.append(PartitionedVertex(0, 4, None))
        subvertices.append(PartitionedVertex(5, 9, None))
        subedges.append(AbstractPartitionedEdge(subvertices[0], subvertices[1]))
        subedges.append(AbstractPartitionedEdge(subvertices[0], PartitionedVertex(0, 100, None)))
        with self.assertRaises(PacmanInvalidParameterException):
            PartitionedGraph(subvertices=subvertices, subedges=subedges)


if __name__ == '__main__':
    unittest.main()
