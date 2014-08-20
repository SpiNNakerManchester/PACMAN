import unittest

#pacman imports
from pacman.model.constraints.abstract_partitioner_constraint import \
    AbstractPartitionerConstraint
from pacman.exceptions import PacmanPlaceException
from pacman.model.partitionable_graph.abstract_partitionable_vertex import \
    AbstractPartitionableVertex
from pacman.model.constraints \
    .vertex_requires_virtual_chip_in_machine_constraint \
    import VertexRequiresVirtualChipInMachineConstraint
from pacman.model.constraints.partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from pacman.model.constraints.partitioner_same_size_as_vertex_constraint \
    import PartitionerSameSizeAsVertexConstraint
from pacman.operations.partition_algorithms.partition_and_place_partitioner \
    import PartitionAndPlacePartitioner
from pacman.operations.placer_algorithms.basic_placer import BasicPlacer
from pacman.exceptions import PacmanPartitionException, \
    PacmanInvalidParameterException
from pacman.model.partitionable_graph.partitionable_graph \
    import PartitionableGraph
from pacman.model.partitionable_graph.partitionable_edge import \
    PartitionableEdge as Edge, PartitionableEdge

#spinn_machine imports
from spinn_machine.machine import Machine
from spinn_machine.processor import Processor
from spinn_machine.sdram import SDRAM
from spinn_machine.link import Link
from spinn_machine.router import Router
from spinn_machine.chip import Chip


class NewPartitionerConstraint(AbstractPartitionerConstraint):

    def __init__(self, label):
        AbstractPartitionerConstraint.__init__(self, label)

    def is_constraint(self):
        return True

    def is_partitioner_constraint(self):
        """ Determine if this is a partitioner constraint
        """
        return True


class Vertex(AbstractPartitionableVertex):

    def __init__(self, n_atoms, label):
        AbstractPartitionableVertex.__init__(self, label=label, n_atoms=n_atoms,
                                             max_atoms_per_core=256)
        self._model_based_max_atoms_per_core = 256

    def get_maximum_atoms_per_core(self):
        return self._model_based_max_atoms_per_core

    @property
    def custom_max_atoms_per_core(self):
        return None

    def model_name(self):
        return "test vertex"

    #Copied from IF_CURR_EXP
    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        return 782 * ((hi_atom - lo_atom) + 1)

    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        return 200 * (hi_atom - lo_atom)

    def get_sdram_usage_for_atoms(self, lo_atom, hi_atom, vertex_in_edges):
        return 4000 + (50 * (hi_atom - lo_atom))


class TestPartitioAndPlacePartitioner(unittest.TestCase):
    def setUp(self):
        self.vert1 = Vertex(10, "New AbstractConstrainedVertex 1")
        self.vert2 = Vertex(5, "New AbstractConstrainedVertex 2")
        self.vert3 = Vertex(3, "New AbstractConstrainedVertex 3")
        self.edge1 = Edge(self.vert1, self.vert2, "First edge")
        self.edge2 = Edge(self.vert2, self.vert1, "Second edge")
        self.edge3 = Edge(self.vert1, self.vert3, "Third edge")
        self.verts = [self.vert1, self.vert2, self.vert3]
        self.edges = [self.edge1, self.edge2, self.edge3]
        self.graph = PartitionableGraph("Graph", self.verts, self.edges)

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

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)

    @staticmethod
    def _print_subvertices(subgraph):
        for subvertex in subgraph.subvertices:
            print subvertex.n_atoms, subvertex.label

    def test_new_partitioner(self):
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        self.assertEqual(partitioner._placer_algorithm, None)
        self.assertEqual(partitioner._placement_to_subvert_mapper, dict())

    def test_set_placer_algorithm(self):
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        self.assertIsInstance(partitioner._placer_algorithm, BasicPlacer)

    def test_invalid_constraints(self):
        with self.assertRaises(PacmanInvalidParameterException):
            constrained_vertex = Vertex(13, "Constrained")
            constrained_vertex.add_constraint(
                VertexRequiresVirtualChipInMachineConstraint((5, 5), (0, 0), 1))
            self.graph.add_vertex(constrained_vertex)
            partitioner = PartitionAndPlacePartitioner(1, 1000)
            partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
            subgraph, graph_to_sub_graph_mapper = \
                    partitioner.partition(self.graph, self.machine)

    def test_valid_constraints(self):
        constrained_vertex = Vertex(5, "Constrained")
        constrained_vertex.add_constraint(PartitionerMaximumSizeConstraint(5))
        self.graph = PartitionableGraph("Graph", [constrained_vertex], [])
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        subgraph, graph_to_sub_graph_mapper = \
                partitioner.partition(self.graph, self.machine)

    def test_operation_with_maximum_size_constraint(self):
        constrained_vertex = Vertex(13, "Constrained")
        constrained_vertex.add_constraint(PartitionerMaximumSizeConstraint(5))
        self.graph = PartitionableGraph("Graph", [constrained_vertex], [])
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        subgraph, graph_to_sub_graph_mapper = \
                partitioner.partition(self.graph, self.machine)
        self.assertEqual(len(subgraph.subvertices), 3)

    def test_operation_with_same_size_as_vertex_constraint(self):
        constrained_vertex = Vertex(5, "Constrained")
        constrained_vertex.add_constraint(
            PartitionerSameSizeAsVertexConstraint(self.vert2))
        self.graph.add_vertex(constrained_vertex)
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        subgraph, graph_to_sub_graph_mapper = \
                partitioner.partition(self.graph, self.machine)
        # self.assertEqual(len(subgraph.subvertices), 3)
        for subv in subgraph.subvertices:
            print subv.n_atoms, subv.label

    def test_operation_with_same_size_as_vertex_constraint_large_vertices(self):
        constrained_vertex = Vertex(300, "Constrained")
        new_large_vertex = Vertex(300, "Non constrained")
        constrained_vertex.add_constraint(
            PartitionerSameSizeAsVertexConstraint(new_large_vertex))
        self.graph = PartitionableGraph("New graph",
                                        [new_large_vertex, constrained_vertex])
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        subgraph, graph_to_sub_graph_mapper = \
                partitioner.partition(self.graph, self.machine)
        # self.assertEqual(len(subgraph.subvertices), 3)
        for subv in subgraph.subvertices:
            print subv.n_atoms, subv.label

    def test_operation_same_size_as_vertex_constraint_different_order(self):
        constrained_vertex = Vertex(300, "Constrained")
        new_large_vertex = Vertex(300, "Non constrained")
        constrained_vertex.add_constraint(
            PartitionerSameSizeAsVertexConstraint(new_large_vertex))
        self.graph = PartitionableGraph("New graph",
                                        [constrained_vertex, new_large_vertex])
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        subgraph, graph_to_sub_graph_mapper = \
                partitioner.partition(self.graph, self.machine)
        # self.assertEqual(len(subgraph.subvertices), 3)
        for subv in subgraph.subvertices:
            print subv.n_atoms, subv.label

    def test_operation_with_same_size_as_vertex_constraint_exception(self):
        with self.assertRaises(PacmanPartitionException):
            constrained_vertex = Vertex(100, "Constrained")
            constrained_vertex.add_constraint(
                PartitionerSameSizeAsVertexConstraint(self.vert2))
            self.graph.add_vertex(constrained_vertex)
            partitioner = PartitionAndPlacePartitioner(1, 1000)
            partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
            subgraph, graph_to_sub_graph_mapper = \
                    partitioner.partition(self.graph, self.machine)

    def test_update_sdram_allocator(self):
        self.assertEqual(True, False)

    def test_add_vertex_constraints_to_subvertex(self):
        self.assertEqual(True, False)

    def test_generate_sub_edges(self):
        self.assertEqual(True, False)

    def test_get_maximum_resources_per_processor(self):
        self.assertEqual(True, False)

    def test_partition_without_setting_placer_algorithm(self):
        with self.assertRaises(PacmanPlaceException):
            partitioner = PartitionAndPlacePartitioner(1, 1000)
            subgraph, graph_to_sub_graph_mapper = \
                partitioner.partition(self.graph, self.machine)

    def test_partition(self):
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        subgraph, graph_to_sub_graph_mapper = \
                partitioner.partition(self.graph, self.machine)
        TestPartitioAndPlacePartitioner._print_subvertices(subgraph)

    def test_detect_subclass_hierarchy(self):
        self.assertEqual(True, False)

    def test_partition_by_atoms(self):
        self.assertEqual(True, False)

    def test_scale_down_resource_usage(self):
        self.assertEqual(True, False)

    def test_scale_up_resource_usage(self):
        self.assertEqual(True, False)

    def test_complete_placements(self):
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        subgraph, graph_to_sub_graph_mapper = \
                partitioner.partition(self.graph, self.machine)
        self.assertEqual(len(subgraph.subvertices), 3)
        for placement in partitioner.complete_placements.placements:
            print placement.subvertex.label, 'x: ', placement.x, 'y:', \
                placement.y, 'p:', placement.p

    def test_complete_placements_for_vertex_spanning_multiple_chips(self):
        monstrous_vertex = Vertex(150 * 25, "Monstrous vertex")
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        self.graph = PartitionableGraph("Graph with monstrous vertex",
                           [monstrous_vertex],
                           [])
        subgraph, graph_to_sub_graph_mapper = \
            partitioner.partition(self.graph, self.machine)
        for placement in partitioner.complete_placements.placements:
            print placement.subvertex.n_atoms, placement.subvertex.label, 'x: ',\
                placement.x, 'y:', placement.y, 'p:', placement.p

    def test_complete_placements_for_almost_full_board(self):
        monstrous_vertex = Vertex(150 * 25 * 17, "Monstrous vertex")
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        self.graph = PartitionableGraph("Graph with monstrous vertex",
                           [monstrous_vertex],
                           [])
        subgraph, graph_to_sub_graph_mapper = \
            partitioner.partition(self.graph, self.machine)
        for placement in partitioner.complete_placements.placements:
            print placement.subvertex.n_atoms, placement.subvertex.label, 'x: ',\
                placement.x, 'y:', placement.y, 'p:', placement.p

    def test_get_max_atoms_per_core(self):
        max_atoms_per_core = PartitionAndPlacePartitioner.\
            _get_max_atoms_per_core(self.verts)
        self.assertEqual(max_atoms_per_core, 256)

    def test_find_max_ratio(self):
        self.assertEqual(True, False)

    def test_locate_vertices_to_partition_now(self):
        self.assertEqual(True, False)

    def test_partition_with_no_additional_constraints(self):
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        subgraph, graph_to_sub_graph_mapper = \
                partitioner.partition(self.graph, self.machine)
        self.assertEqual(len(subgraph.subvertices), 3)
        vert_sizes = []
        for vert in self.verts:
            vert_sizes.append(vert.n_atoms)
        self.assertEqual(len(subgraph.subedges), 3)
        for subvert in subgraph.subvertices:
            self.assertIn(subvert.n_atoms, vert_sizes)

    def test_partition_with_no_additional_constraints_extra_edge(self):
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        subgraph, graph_to_sub_graph_mapper = \
            partitioner.partition(self.graph, self.machine)
        self.assertEqual(len(subgraph.subvertices), 3)
        self.assertEqual(len(subgraph.subedges), 4)

    def test_partition_on_large_vertex_than_has_to_be_split(self):
        large_vertex = Vertex(300, "Large vertex")
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        self.graph = PartitionableGraph("Graph with large vertex",
                           [large_vertex],
                           [])
        subgraph, graph_to_sub_graph_mapper = \
            partitioner.partition(self.graph, self.machine)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(subgraph.subvertices), 1)
        for subv in subgraph.subvertices:
            print subv.n_atoms, subv.label

    def test_partition_on_very_large_vertex_than_has_to_be_split(self):
        large_vertex = Vertex(500, "Large vertex")
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = PartitionableGraph("Graph with large vertex",
                           [large_vertex],
                           [])
        subgraph, graph_to_sub_graph_mapper = \
            partitioner.partition(self.graph, self.machine)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(subgraph.subvertices), 1)
        for subv in subgraph.subvertices:
            print subv.n_atoms, subv.label

    def test_partition_on_target_size_vertex_than_has_to_be_split(self):
        large_vertex = Vertex(1000, "Large vertex")
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = PartitionableGraph("Graph with large vertex",
                           [large_vertex],
                           [])
        subgraph, graph_to_sub_graph_mapper = \
            partitioner.partition(self.graph, self.machine)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(subgraph.subvertices), 1)
        for subv in subgraph.subvertices:
            print subv.n_atoms, subv.label

    def test_partition_with_supported_constraints_enough_space(self):
        self.assertEqual(True, False)

    def test_partition_with_supported_constraints_not_enough_space(self):
        self.assertEqual(True, False)


    def test_partition_with_barely_sufficient_space(self):
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(2**12)

        links = list()

        links.append(Link(0, 0, 0, 1, 1, n, n))
        links.append(Link(0, 1, 1, 1, 0, s, s))
        links.append(Link(1, 1, 2, 0, 0, e, e))
        links.append(Link(1, 0, 3, 0, 1, w, w))
        r = Router(links, False, 100, 1024)

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)
        singular_vertex = Vertex(1, "Large vertex")
        self.assertEqual(singular_vertex._model_based_max_atoms_per_core, 256)
        self.graph = PartitionableGraph("Graph with large vertex",
                           [singular_vertex], [])
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        subgraph, graph_to_sub_graph_mapper = \
            partitioner.partition(self.graph, self.machine)
        self.assertEqual(singular_vertex._model_based_max_atoms_per_core, 256)
        self.assertEqual(len(subgraph.subvertices), 1)

        for subv in subgraph.subvertices:
            print subv.n_atoms, subv.label

    def test_partition_with_insufficient_space(self):
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(2**11)

        links = list()

        links.append(Link(0, 0, 0, 1, 1, n, n))
        links.append(Link(0, 1, 1, 1, 0, s, s))
        links.append(Link(1, 1, 2, 0, 0, e, e))
        links.append(Link(1, 0, 3, 0, 1, w, w))
        r = Router(links, False, 100, 1024)

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)
        large_vertex = Vertex(300, "Large vertex")
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = PartitionableGraph("Graph with large vertex",
                           [large_vertex],
                           [])
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        with self.assertRaises(PacmanPartitionException):
            subgraph, graph_to_sub_graph_mapper = \
                partitioner.partition(self.graph, self.machine)

    def test_partition_with_less_sdram_than_default(self):
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(128*(2**19))

        links = list()

        links.append(Link(0, 0, 0, 1, 1, n, n))
        links.append(Link(0, 1, 1, 1, 0, s, s))
        links.append(Link(1, 1, 2, 0, 0, e, e))
        links.append(Link(1, 0, 3, 0, 1, w, w))
        r = Router(links, False, 100, 1024)

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        subgraph, graph_to_sub_graph_mapper = \
            partitioner.partition(self.graph, self.machine)

    def test_partition_with_more_sdram_than_default(self):
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(128*(2**22))

        links = list()

        links.append(Link(0, 0, 0, 1, 1, n, n))
        links.append(Link(0, 1, 1, 1, 0, s, s))
        links.append(Link(1, 1, 2, 0, 0, e, e))
        links.append(Link(1, 0, 3, 0, 1, w, w))
        r = Router(links, False, 100, 1024)

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        subgraph, graph_to_sub_graph_mapper = \
            partitioner.partition(self.graph, self.machine)

    def test_partition_with_unsupported_constraints(self):
        with self.assertRaises(PacmanInvalidParameterException):
            constrained_vertex = Vertex(13, "Constrained")
            constrained_vertex.add_constraint(NewPartitionerConstraint(
                "Custom unsupported constraint"))
            self.graph.add_vertex(constrained_vertex)
            partitioner = PartitionAndPlacePartitioner(1, 1000)
            partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
            subgraph, graph_to_sub_graph_mapper = \
                    partitioner.partition(self.graph, self.machine)

    def test_partition_with_one_vertex_with_unsupported_constraint(self):
        with self.assertRaises(PacmanInvalidParameterException):
            constrained_vertex = Vertex(13, "Constrained")
            constrained_vertex.add_constraint(NewPartitionerConstraint(
                "Custom unsupported constraint"))
            self.graph = PartitionableGraph("Solo graph", [constrained_vertex])
            partitioner = PartitionAndPlacePartitioner(1, 1000)
            partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
            subgraph, graph_to_sub_graph_mapper = \
                    partitioner.partition(self.graph, self.machine)

    def test_partition_with_empty_graph(self):
        self.graph = PartitionableGraph()
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        subgraph, graph_to_sub_graph_mapper = \
            partitioner.partition(self.graph, self.machine)
        self.assertEqual(len(subgraph.subvertices), 0)

if __name__ == '__main__':
    #t1 = TestPartitioAndPlacePartitioner()
    #t1.setUp()
    #t1.test_partition_on_large_vertex_than_has_to_be_split()
    unittest.main()
