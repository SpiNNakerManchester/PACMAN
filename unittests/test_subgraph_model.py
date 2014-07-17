import unittest
from pacman.model.subgraph.subvertex import Subvertex
from pacman.model.subgraph.subgraph import Subgraph
from pacman.model.subgraph.subedge import Subedge
from pacman.model.graph.graph import Graph, Vertex, Edge
from pacman.exceptions import PacmanInvalidParameterException
class MyVertex(Vertex):
    def get_resources_used_by_atoms(self, lo_atom, hi_atom,
                                    number_of_machine_time_steps):
        pass

class TestSubgraphModel(unittest.TestCase):
    def test_new_vertex(self):
        vert = MyVertex(10, 'vertex')
        subvert = Subvertex(0,9)

    def test_new_vertex_lo_eq_hi(self):
        vert = MyVertex(10, 'vertex')
        subvert = Subvertex(5,5)

    def test_new_vertex_lo_gt_hi(self):
        with self.assertRaises(PacmanInvalidParameterException):
            subvert = Subvertex(9,0)

    def test_new_subgraph(self):
        subvertices = list()
        subedges = list()
        for i in range(10):
            subvertices.append(Subvertex(0,4))
        for i in range(5):
            subedges.append(Subedge(subvertices[0],subvertices[(i+1)]))
        for i in range(5,10):
            subedges.append(Subedge(subvertices[5],subvertices[(i+1)%10]))
        subgraph = Subgraph(None, subvertices, subedges)
        outgoing = subgraph.outgoing_subedges_from_subvertex(subvertices[0])
        for i in range(5):
            if subedges[i] not in outgoing:
                raise AssertionError("subedges[" + str(i) +  "] is not in outgoing and should be")
        for i in range(5,10):
            if subedges[i] in outgoing:
                raise AssertionError("subedges[" + str(i) +  "] is in outgoing and shouldn't be")

        incoming = subgraph.incoming_subedges_from_subvertex(subvertices[0])

        if subedges[9] not in incoming:
            raise AssertionError("subedges[" + str(i) +  "] is not in incoming and should be")
        for i in range(9):
            if subedges[i] in incoming:
                raise AssertionError("subedges[" + str(i) +  "] is in incoming and shouldn't be")

        subvertices_from_subgraph = subgraph.subvertices
        subvedges_from_subgraph = subgraph.subedges
        for i in range(10):
            self.assertEqual(subvertices[i], subvertices_from_subgraph[i])
            self.assertEqual(subedges[i],subvedges_from_subgraph[i])



    def test_new_empty_subgraph(self):
        Subgraph()
if __name__ == '__main__':
    unittest.main()
