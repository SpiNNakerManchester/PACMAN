import unittest
from pacman.model.subgraph.subvertex import Subvertex
from pacman.model.subgraph.subgraph import Subgraph
from pacman.model.subgraph.subedge import Subedge
from pacman.exceptions import PacmanInvalidParameterException
from pacman.exceptions import PacmanAlreadyExistsException


class TestSubgraphModel(unittest.TestCase):
    def test_new_vertex(self):
        Subvertex(0, 9)

    def test_new_vertex_lo_eq_hi(self):
        Subvertex(5, 5)

    def test_new_vertex_lo_gt_hi(self):
        with self.assertRaises(PacmanInvalidParameterException):
            Subvertex(9, 0)

    def test_new_empty_subgraph(self):
        Subgraph()

    def test_new_subgraph(self):
        subvertices = list()
        subedges = list()
        for i in range(10):
            subvertices.append(Subvertex(0, 4))
        for i in range(5):
            subedges.append(Subedge(subvertices[0], subvertices[(i + 1)]))
        for i in range(5, 10):
            subedges.append(Subedge(subvertices[5], subvertices[(i + 1) % 10]))
        subgraph = Subgraph(subvertices=subvertices, subedges=subedges)
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
        with self.assertRaises(PacmanAlreadyExistsException):
            subvertices = list()
            subedges = list()
            subv = Subvertex(0, 4)
            subvertices.append(subv)
            subvertices.append(Subvertex(5, 9))
            subvertices.append(subv)
            subedges.append(Subedge(subvertices[0], subvertices[1]))
            subedges.append(Subedge(subvertices[1], subvertices[0]))
            Subgraph(subvertices=subvertices, subedges=subedges)

    def test_add_duplicate_subedge(self):
        with self.assertRaises(PacmanAlreadyExistsException):
            subvertices = list()
            subedges = list()
            subvertices.append(Subvertex(5, 9))
            subvertices.append(Subvertex(5, 9))
            sube = Subedge(subvertices[0], subvertices[1])
            subedges.append(sube)
            subedges.append(sube)
            Subgraph(subvertices=subvertices, subedges=subedges)

    def test_add_subedge_with_no_existing_pre_subvertex_in_subgraph(self):
        with self.assertRaises(PacmanInvalidParameterException):
            subvertices = list()
            subedges = list()
            subvertices.append(Subvertex(0, 4))
            subvertices.append(Subvertex(5, 9))
            subedges.append(Subedge(subvertices[0], subvertices[1]))
            subedges.append(Subedge(Subvertex(0, 100), subvertices[0]))
            Subgraph(subvertices=subvertices, subedges=subedges)

    def test_add_subedge_with_no_existing_post_subvertex_in_subgraph(self):
        with self.assertRaises(PacmanInvalidParameterException):
            subvertices = list()
            subedges = list()
            subvertices.append(Subvertex(0, 4))
            subvertices.append(Subvertex(5, 9))
            subedges.append(Subedge(subvertices[0], subvertices[1]))
            subedges.append(Subedge(subvertices[0], Subvertex(0, 100)))
            Subgraph(subvertices=subvertices, subedges=subedges)


if __name__ == '__main__':
    unittest.main()
