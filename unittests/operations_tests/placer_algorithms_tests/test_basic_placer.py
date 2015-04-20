"""
test basic placer
"""

# pacman imports
from pacman.model.partitionable_graph.multi_cast_partitionable_edge import \
    MultiCastPartitionableEdge
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import \
    PlacerChipAndCoreConstraint
from pacman.exceptions import PacmanPlaceException
from pacman.model.partitioned_graph.partitioned_vertex \
    import PartitionedVertex
from pacman.model.graph_mapper.graph_mapper import GraphMapper
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.model.partitionable_graph.partitionable_graph \
    import PartitionableGraph
from pacman.operations.placer_algorithms.basic_placer import BasicPlacer

# spinn machine imports
from spinn_machine.chip import Chip
from spinn_machine.link import Link
from spinn_machine.machine import Machine
from spinn_machine.processor import Processor
from spinn_machine.router import Router
from spinn_machine.sdram import SDRAM

# general imports
import unittest
from uinit_test_objects.test_vertex import TestVertex


class TestBasicPlacer(unittest.TestCase):
    """
    test for basic placement algorithum
    """
    def setUp(self):
        ########################################################################
        # Setting up vertices, edges and graph                                 #
        ########################################################################
        self.vert1 = TestVertex(100, "New AbstractConstrainedTestVertex 1")
        self.vert2 = TestVertex(5, "New AbstractConstrainedTestVertex 2")
        self.vert3 = TestVertex(3, "New AbstractConstrainedTestVertex 3")
        self.edge1 = MultiCastPartitionableEdge(self.vert1, self.vert2, 
                                                "First edge")
        self.edge2 = MultiCastPartitionableEdge(self.vert2, self.vert1, 
                                                "Second edge")
        self.edge3 = MultiCastPartitionableEdge(self.vert1, self.vert3, 
                                                "Third edge")
        self.verts = [self.vert1, self.vert2, self.vert3]
        self.edges = [self.edge1, self.edge2, self.edge3]
        self.graph = PartitionableGraph("Graph", self.verts, self.edges)

        ########################################################################
        # Setting up machine                                                   #
        ########################################################################
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        _sdram = SDRAM(128 * (2**20))

        ip = "192.168.240.253"
        chips = list()
        for x in range(10):
            for y in range(10):
                links = list()

                links.append(Link(x, y, 0, (x + 1) % 10, y, n, n))
                links.append(Link(x, y, 1, (x + 1) % 10, (y + 1) % 10, s, s))
                links.append(Link(x, y, 2, x, (y + 1) % 10, n, n))
                links.append(Link(x, y, 3, (x - 1) % 10, y, s, s))
                links.append(Link(x, y, 4, (x - 1) % 10, (y - 1) % 10, n, n))
                links.append(Link(x, y, 5, x, (y - 1) % 10, s, s))

                r = Router(links, False, 100, 1024)
                chips.append(Chip(x, y, processors, r, _sdram, 0, 0, ip))

        self.machine = Machine(chips)
        ########################################################################
        # Setting up subgraph and graph_mapper                                 #
        ########################################################################
        self.subvertices = list()
        self.subvertex1 = PartitionedVertex(
            0, 1, self.vert1.get_resources_used_by_atoms(0, 1, []),
            "First subvertex")
        self.subvertex2 = PartitionedVertex(
            1, 5, get_resources_used_by_atoms(1, 5, []), "Second subvertex")
        self.subvertex3 = PartitionedVertex(
            5, 10, get_resources_used_by_atoms(5, 10, []), "Third subvertex")
        self.subvertex4 = PartitionedVertex(
            10, 100, get_resources_used_by_atoms(10, 100, []),
            "Fourth subvertex")
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

    def test_place_where_subvertices_dont_have_vertex(self):
        self.bp = BasicPlacer(self.machine, self.graph)
        placements = self.bp.place(self.subgraph, self.graph_mapper)
        for placement in placements.placements:
            print placement.subvertex.label, placement.subvertex.n_atoms, \
                'x:', placement.x, 'y:', placement.y, 'p:', placement.p

    def test_place_where_subvertices_have_vertices(self):
        self.bp = BasicPlacer(self.machine, self.graph)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices(self.subvertices, self.vert1)
        placements = self.bp.place(self.subgraph, self.graph_mapper)
        for placement in placements.placements:
            print placement.subvertex.label, placement.subvertex.n_atoms, \
                'x:', placement.x, 'y:', placement.y, 'p:', placement.p

    def test_place_subvertex_too_big_with_vertex(self):
        large_vertex = TestVertex(500, "Large vertex 500")
        large_subvertex = large_vertex.create_subvertex(
            0, 499, get_resources_used_by_atoms(0, 499, []))#PartitionedVertex(0, 499, "Large subvertex")
        self.graph.add_vertex(large_vertex)
        self.graph = PartitionableGraph("Graph",[large_vertex])
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices([large_subvertex], large_vertex)
        self.bp = BasicPlacer(self.machine, self.graph)
        self.subgraph = PartitionedGraph(subvertices=[large_subvertex])
        with self.assertRaises(PacmanPlaceException):
            placements = self.bp.place(self.subgraph, self.graph_mapper)

    def test_try_to_place(self):
        self.assertEqual(True, False, "Test not implemented yet")

    def test_deal_with_constraint_placement_subvertices_dont_have_vertex(self):
        self.bp = BasicPlacer(self.machine, self.graph)
        self.subvertex1.add_constraint(PlacerChipAndCoreConstraint(8, 3, 2))
        self.assertIsInstance(self.subvertex1.constraints[0], PlacerChipAndCoreConstraint)
        self.subvertex2.add_constraint(PlacerChipAndCoreConstraint(3, 5, 7))
        self.subvertex3.add_constraint(PlacerChipAndCoreConstraint(2, 4, 6))
        self.subvertex4.add_constraint(PlacerChipAndCoreConstraint(6, 4, 16))
        self.subvertices = list()
        self.subvertices.append(self.subvertex1)
        self.subvertices.append(self.subvertex2)
        self.subvertices.append(self.subvertex3)
        self.subvertices.append(self.subvertex4)
        self.subedges = list()
        self.subgraph = PartitionedGraph("Subgraph", self.subvertices,
                                         self.subedges)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices(self.subvertices)
        placements = self.bp.place(self.subgraph, self.graph_mapper)
        for placement in placements.placements:
            print placement.subvertex.label, placement.subvertex.n_atoms, \
                'x:', placement.x, 'y:', placement.y, 'p:', placement.p

    def test_deal_with_constraint_placement_subvertices_have_vertices(self):
        self.bp = BasicPlacer(self.machine, self.graph)
        self.subvertex1.add_constraint(PlacerChipAndCoreConstraint(1, 5, 2))
        self.assertIsInstance(self.subvertex1.constraints[0], PlacerChipAndCoreConstraint)
        self.subvertex2.add_constraint(PlacerChipAndCoreConstraint(3, 5, 7))
        self.subvertex3.add_constraint(PlacerChipAndCoreConstraint(2, 4, 6))
        self.subvertex4.add_constraint(PlacerChipAndCoreConstraint(6, 7, 16))
        self.subvertices = list()
        self.subvertices.append(self.subvertex1)
        self.subvertices.append(self.subvertex2)
        self.subvertices.append(self.subvertex3)
        self.subvertices.append(self.subvertex4)
        self.subedges = list()
        self.subgraph = PartitionedGraph("Subgraph", self.subvertices,
                                         self.subedges)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices(self.subvertices, self.vert1)
        placements = self.bp.place(self.subgraph, self.graph_mapper)
        for placement in placements.placements:
            print placement.subvertex.label, placement.subvertex.n_atoms, \
                'x:', placement.x, 'y:', placement.y, 'p:', placement.p

    def test_unsupported_non_placer_constraint(self):
        self.assertEqual(True, False, "Test not implemented yet")

    def test_unsupported_placer_constraint(self):
        self.assertEqual(True, False, "Test not implemented yet")

    def test_unsupported_placer_constraints(self):
        self.assertEqual(True, False, "Test not implemented yet")

    def test_many_subvertices(self):
        subvertices = list()
        for i in range(20 * 17): #50 atoms per each processor on 20 chips
            subvertices.append(PartitionedTestVertex(
                0, 50, get_resources_used_by_atoms(0, 50, []),
                "PartitionedVertex " + str(i)))

        self.graph = PartitionableGraph("Graph",subvertices)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices(subvertices)
        self.bp = BasicPlacer(self.machine, self.graph)
        self.subgraph = PartitionedGraph(subvertices=subvertices)
        placements = self.bp.place(self.subgraph, self.graph_mapper)
        for placement in placements.placements:
            print placement.subvertex.label, placement.subvertex.n_atoms, \
                'x:', placement.x, 'y:', placement.y, 'p:', placement.p

    def test_too_many_subvertices(self):
        subvertices = list()
        for i in range(100 * 17): #50 atoms per each processor on 20 chips
            subvertices.append(PartitionedTestVertex(
                0, 50, get_resources_used_by_atoms(0, 50, []),
                "PartitionedVertex " + str(i)))

        self.graph = PartitionableGraph("Graph",subvertices)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices(subvertices)
        self.bp = BasicPlacer(self.machine, self.graph)
        self.subgraph = PartitionedGraph(subvertices=subvertices)
        with self.assertRaises(PacmanPlaceException):
            placements = self.bp.place(self.subgraph, self.graph_mapper)

    def test_fill_machine(self):
        subvertices = list()
        for i in range(99 * 17): #50 atoms per each processor on 20 chips
            subvertices.append(PartitionedTestVertex(
                0, 50, get_resources_used_by_atoms(0, 50, []),
                "PartitionedVertex " + str(i)))

        self.graph = PartitionableGraph("Graph",subvertices)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices(subvertices)
        self.bp = BasicPlacer(self.machine, self.graph)
        self.subgraph = PartitionedGraph(subvertices=subvertices)
        placements = self.bp.place(self.subgraph, self.graph_mapper)
    
if __name__ == '__main__':
    unittest.main()
