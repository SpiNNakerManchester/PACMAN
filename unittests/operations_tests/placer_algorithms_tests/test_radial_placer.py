import unittest

from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.model.constraints.placer_constraints.placer_chip_and_core_constraint import \
    PlacerChipAndCoreConstraint
from pacman.exceptions import PacmanPlaceException
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.graph_mapper.graph_mapper import GraphMapper
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.model.partitionable_graph.abstract_partitionable_edge\
    import AbstractPartitionableEdge
from pacman.model.partitionable_graph.partitionable_graph import PartitionableGraph
from pacman.model.partitionable_graph.abstract_partitionable_vertex import \
    AbstractPartitionableVertex
from pacman.operations.placer_algorithms.radial_placer import RadialPlacer
from spinn_machine.chip import Chip
from spinn_machine.link import Link
from spinn_machine.machine import Machine
from spinn_machine.processor import Processor
from spinn_machine.router import Router
from spinn_machine.sdram import SDRAM


def get_resources_used_by_atoms(lo_atom, hi_atom, vertex_in_edges):
    vertex = Vertex(1, None)
    cpu_cycles = vertex.get_cpu_usage_for_atoms(lo_atom, hi_atom)
    dtcm_requirement = vertex.get_dtcm_usage_for_atoms(lo_atom, hi_atom)
    sdram_requirement = vertex.get_sdram_usage_for_atoms(
        lo_atom, hi_atom, vertex_in_edges)
    # noinspection PyTypeChecker
    resources = ResourceContainer(cpu=CPUCyclesPerTickResource(cpu_cycles),
                                  dtcm=DTCMResource(dtcm_requirement),
                                  sdram=SDRAMResource(sdram_requirement))
    return resources


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

    def get_sdram_usage_for_atoms(
            self, vertex_slice, partitionable_graph):
        return 4000 + (50 * (vertex_slice.hi_atom - vertex_slice.lo_atom))

class Subvertex(PartitionedVertex):

    def __init__(self, lo_atom, hi_atom, resources_required, label=None,
                 constraints=None):
        PartitionedVertex.__init__(self, lo_atom, hi_atom, resources_required,
                                   label=label, constraints=constraints)
        self._model_based_max_atoms_per_core = 256


class TestRadialPlacer(unittest.TestCase):
    def setUp(self):
        ########################################################################
        #Setting up vertices, edges and graph                                  #
        ########################################################################
        self.vert1 = Vertex(100, "New AbstractConstrainedVertex 1")
        self.vert2 = Vertex(5, "New AbstractConstrainedVertex 2")
        self.vert3 = Vertex(3, "New AbstractConstrainedVertex 3")
        self.edge1 = AbstractPartitionableEdge(self.vert1, self.vert2, "First edge")
        self.edge2 = AbstractPartitionableEdge(self.vert2, self.vert1, "Second edge")
        self.edge3 = AbstractPartitionableEdge(self.vert1, self.vert3, "Third edge")
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

        _sdram = SDRAM(128*(2**20))



        ip = "192.168.240.253"
        chips = list()
        for x in range(10):
            for y in range(10):
                links = list()

                links.append(Link(x, y, 0, (x + 1)%10, y, n, n))
                links.append(Link(x, y, 1, (x + 1)%10, (y + 1)%10 , s, s))
                links.append(Link(x, y, 2, x, (y + 1)%10, n, n))
                links.append(Link(x, y, 3, (x - 1)%10, y, s, s))
                links.append(Link(x, y, 4, (x - 1)%10, (y - 1)%10, n, n))
                links.append(Link(x, y, 5, x, (y - 1)%10, s, s))

                r = Router(links, False, 100, 1024)
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)
        ########################################################################
        #Setting up subgraph and graph_mapper                                  #
        ########################################################################
        self.subvertices = list()
        self.subvertex1 = Subvertex(
            0, 1, get_resources_used_by_atoms(0, 1, []), "First subvertex")
        self.subvertex2 = Subvertex(
            1, 5, get_resources_used_by_atoms(1, 5, []), "Second subvertex")
        self.subvertex3 = Subvertex(
            5, 10, get_resources_used_by_atoms(5, 10, []), "Third subvertex")
        self.subvertex4 = Subvertex(
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

    @unittest.skip("demonstrating skipping")
    def test_new_basic_placer(self):
        self.bp = RadialPlacer(self.machine, self.graph)
        self.assertEqual(self.bp._machine, self.machine)
        self.assertEqual(self.bp._graph, self.graph)

    @unittest.skip("demonstrating skipping")
    def test_place_where_subvertices_dont_have_vertex(self):
        self.bp = RadialPlacer(self.machine, self.graph)
        placements = self.bp.place(self.subgraph, self.graph_mapper)
        for placement in placements.placements:
            print placement.subvertex.label, placement.subvertex.n_atoms, \
                'x:', placement.x, 'y:', placement.y, 'p:', placement.p

    @unittest.skip("demonstrating skipping")
    def test_place_where_subvertices_have_vertices(self):
        self.bp = RadialPlacer(self.machine, self.graph)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices(self.subvertices, self.vert1)
        placements = self.bp.place(self.subgraph, self.graph_mapper)
        for placement in placements.placements:
            print placement.subvertex.label, placement.subvertex.n_atoms, \
                'x:', placement.x, 'y:', placement.y, 'p:', placement.p

    @unittest.skip("demonstrating skipping")
    def test_place_subvertex_too_big_with_vertex(self):
        large_vertex = Vertex(500, "Large vertex 500")
        large_subvertex = large_vertex.create_subvertex(
            0, 499, get_resources_used_by_atoms(0, 499, []))#Subvertex(0, 499, "Large subvertex")
        self.graph.add_vertex(large_vertex)
        self.graph = PartitionableGraph("Graph",[large_vertex])
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices([large_subvertex], large_vertex)
        self.bp = RadialPlacer(self.machine, self.graph)
        self.subgraph = PartitionedGraph(subvertices=[large_subvertex])
        with self.assertRaises(PacmanPlaceException):
            placements = self.bp.place(self.subgraph, self.graph_mapper)

    @unittest.skip("demonstrating skipping")
    def test_try_to_place(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("demonstrating skipping")
    def test_deal_with_constraint_placement_subvertices_dont_have_vertex(self):
        self.bp = RadialPlacer(self.machine, self.graph)
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

    @unittest.skip("demonstrating skipping")
    def test_deal_with_constraint_placement_subvertices_have_vertices(self):
        self.bp = RadialPlacer(self.machine, self.graph)
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

    @unittest.skip("demonstrating skipping")
    def test_unsupported_non_placer_constraint(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("demonstrating skipping")
    def test_unsupported_placer_constraint(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("demonstrating skipping")
    def test_unsupported_placer_constraints(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("demonstrating skipping")
    def test_many_subvertices(self):
        subvertices = list()
        for i in range(20 * 17): #51 atoms per each processor on 20 chips
            subvertices.append(PartitionedVertex(
                0, 50, get_resources_used_by_atoms(0, 50, []),
                "Subvertex " + str(i)))

        self.graph = PartitionableGraph("Graph",subvertices)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices(subvertices)
        self.bp = RadialPlacer(self.machine, self.graph)
        self.subgraph = PartitionedGraph(subvertices=subvertices)
        placements = self.bp.place(self.subgraph, self.graph_mapper)
        unorderdered_info = list()
        for placement in placements.placements:
            unorderdered_info.append(
                (placement.subvertex.label.split(" ")[0],
                "{:<4}".format(placement.subvertex.label.split(" ")[1]),
                 placement.subvertex.n_atoms, 'x: ',
                 placement.x, 'y: ', placement.y, 'p: ', placement.p))

        from operator import itemgetter
        sorted_info = sorted(unorderdered_info, key=itemgetter(4, 6, 8))
        from pprint import pprint as pp
        pp(sorted_info)

        pp("{}".format("=" * 50))
        sorted_info = sorted(unorderdered_info, key=lambda x: int(x[1]))
        pp(sorted_info)

    @unittest.skip("demonstrating skipping")
    def test_too_many_subvertices(self):
        subvertices = list()
        for i in range(100 * 17): #50 atoms per each processor on 20 chips
            subvertices.append(PartitionedVertex(
                0, 50, get_resources_used_by_atoms(0, 50, []),
                "Subvertex " + str(i)))

        self.graph = PartitionableGraph("Graph",subvertices)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices(subvertices)
        self.bp = RadialPlacer(self.machine, self.graph)
        self.subgraph = PartitionedGraph(subvertices=subvertices)
        with self.assertRaises(PacmanPlaceException):
            placements = self.bp.place(self.subgraph, self.graph_mapper)

    @unittest.skip("demonstrating skipping")
    def test_fill_machine(self):
        subvertices = list()
        for i in range(99 * 17): #50 atoms per each processor on 20 chips
            subvertices.append(PartitionedVertex(
                0, 50, get_resources_used_by_atoms(0, 50, []),
                "Subvertex " + str(i)))

        self.graph = PartitionableGraph("Graph",subvertices)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_subvertices(subvertices)
        self.bp = RadialPlacer(self.machine, self.graph)
        self.subgraph = PartitionedGraph(subvertices=subvertices)
        placements = self.bp.place(self.subgraph, self.graph_mapper)

if __name__ == '__main__':
    unittest.main()
