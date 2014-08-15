import unittest
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.graph_mapper.graph_mapper import GraphMapper
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.model.partitionable_graph.partitionable_edge import PartitionableEdge
from pacman.model.partitionable_graph.partitionable_graph import PartitionableGraph
from pacman.model.partitionable_graph.abstract_partitionable_vertex import \
    AbstractPartitionableVertex
from pacman.operations.placer_algorithms.basic_placer import BasicPlacer
from spinn_machine.chip import Chip
from spinn_machine.link import Link
from spinn_machine.machine import Machine
from spinn_machine.processor import Processor
from spinn_machine.router import Router
from spinn_machine.sdram import SDRAM


class Vertex(AbstractPartitionableVertex):

    def __init__(self, n_atoms, label):
        AbstractPartitionableVertex.__init__(self, label=label, n_atoms=n_atoms,
                                             max_atoms_per_core=256)
        self._model_based_max_atoms_per_core = 256

    def model_name(self):
        return "test vertex"

    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        return 10 * (hi_atom - lo_atom)

    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        return 200 * (hi_atom - lo_atom)

    def get_sdram_usage_for_atoms(self, lo_atom, hi_atom, vertex_in_edges):
        return 4000 + (50 * (hi_atom - lo_atom))

class Subvertex(PartitionedVertex):

    def __init__(self, lo_atom, hi_atom, label=None, constraints=None):
        PartitionedVertex.__init__(self, lo_atom, hi_atom,
                                   label=label, constraints=constraints)
        self._model_based_max_atoms_per_core = 256


class TestBasicPlacer(unittest.TestCase):
    def setUp(self):
        ########################################################################
        #Setting up vertices, edges and graph                                  #
        ########################################################################
        self.vert1 = Vertex(100, "New AbstractConstrainedVertex 1")
        self.vert2 = Vertex(5, "New AbstractConstrainedVertex 2")
        self.vert3 = Vertex(3, "New AbstractConstrainedVertex 3")
        self.edge1 = PartitionableEdge(self.vert1, self.vert2, "First edge")
        self.edge2 = PartitionableEdge(self.vert2, self.vert1, "Second edge")
        self.edge3 = PartitionableEdge(self.vert1, self.vert3, "Third edge")
        self.verts = [self.vert1, self.vert2, self.vert3]
        self.edges = [self.edge1, self.edge2, self.edge3]
        self.graph = PartitionableGraph("Graph", self.verts, self.edges)

        ########################################################################
        #Setting up machine                                                    #
        ########################################################################
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(128*(2**20))

        links = list()

        links.append(Link(0, 0, 0, 1, 1, n, n))
        links.append(Link(0, 1, 1, 1, 0, s, s))
        links.append(Link(1, 1, 2, 0, 0, e, e))
        links.append(Link(1, 0, 3, 0, 1, w, w))
        r = Router(links, False, 100, 1024)

        ip = "192.168.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)
        ########################################################################
        #Setting up subgraph and graph_mapper                                  #
        ########################################################################
        self.subvertices = list()
        self.subvertex1 = Subvertex(0, 1, "First subvertex")
        self.subvertex2 = Subvertex(1, 5, "Second subvertex")
        self.subvertex3 = Subvertex(5, 10, "Third subvertex")
        self.subvertex4 = Subvertex(10, 100, "Fourth subvertex")
        self.subvertices.append(self.subvertex1)
        self.subvertices.append(self.subvertex2)
        self.subvertices.append(self.subvertex3)
        self.subvertices.append(self.subvertex4)
        self.subedges = list()
        self.subgraph = PartitionedGraph("Subgraph", self.subvertices,
                                         self.subedges)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices(self.subvertices)


    def test_new_basic_placer(self):
        self.bp = BasicPlacer(self.machine, self.graph)
        self.assertEqual(self.bp._machine, self.machine)
        self.assertEqual(self.bp._graph, self.graph)

    def test_place(self):
        self.bp = BasicPlacer(self.machine, self.graph)
        placements = self.bp.place(self.subgraph, self.graph_mapper)
        print placements.placements
        print "############################################"
        for subvertex in self.subvertices:
            print placements.get_placement_of_subvertex(subvertex).subvertex, \
                placements.get_placement_of_subvertex(subvertex).x, \
                placements.get_placement_of_subvertex(subvertex).y, \
                placements.get_placement_of_subvertex(subvertex).p

    def test_place_where_subvertices_have_vertices(self):
        self.bp = BasicPlacer(self.machine, self.graph)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices(self.subvertices, self.vert1)
        placements = self.bp.place(self.subgraph, self.graph_mapper)
        print placements.placements
        print "############################################"
        for subvertex in self.subvertices:
            print placements.get_placement_of_subvertex(subvertex).subvertex, \
                placements.get_placement_of_subvertex(subvertex).x, \
                placements.get_placement_of_subvertex(subvertex).y, \
                placements.get_placement_of_subvertex(subvertex).p

    def test_place_subvertex_too_big_with_vertex(self):
        large_vertex = Vertex(500, "Large vertex 500")
        large_subvertex = large_vertex.create_subvertex(0, 499)#Subvertex(0, 499, "Large subvertex")
        self.graph.add_vertex(large_vertex)
        self.graph = PartitionableGraph("Graph",[large_vertex])
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices([large_subvertex], large_vertex)
        self.bp = BasicPlacer(self.machine, self.graph)
        placements = self.bp.place(self.subgraph, self.graph_mapper)
        print placements.placements
        print "############################################"
        for subvertex in self.subvertices:
            print placements.get_placement_of_subvertex(subvertex).subvertex, \
                placements.get_placement_of_subvertex(subvertex).x, \
                placements.get_placement_of_subvertex(subvertex).y, \
                placements.get_placement_of_subvertex(subvertex).p



    def test_place_subvertex(self):
        self.assertEqual(True, False)

    def test_try_to_place(self):
        self.assertEqual(True, False)

    def test_deal_with_constraint_placement(self):
        self.assertEqual(True, False)

    def test_deal_with_non_constrainted_placement(self):
        self.assertEqual(True, False)

    def test_unsupported_non_placer_constraint(self):
        self.assertEqual(True, False)

    def test_unsupported_placer_constraint(self):
        self.assertEqual(True, False)

    def test_unsupported_placer_constraints(self):
        self.assertEqual(True, False)



if __name__ == '__main__':
    unittest.main()
