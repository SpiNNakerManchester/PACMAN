import unittest
from pacman.model.constraints.abstract_partitioner_constraint import \
    AbstractPartitionerConstraint
from pacman.model\
    .constraints.vertex_requires_virtual_chip_in_machine_constraint import \
    VertexRequiresVirtualChipInMachineConstraint
from pacman.model.partitionable_graph.abstract_partitionable_vertex import \
    AbstractPartitionableVertex
from pacman.exceptions import PacmanPartitionException, \
    PacmanInvalidParameterException
from pacman.operations.partition_algorithms.basic_partitioner \
    import BasicPartitioner
from pacman.model.partitionable_graph.partitionable_graph \
    import PartitionableGraph
from spynnaker.pyNN.models.neural_models.if_curr_exp \
    import IFCurrentExponentialPopulation as IFCurrVertex
from pacman.model.partitionable_graph.partitionable_edge \
    import PartitionableEdge
from spinn_machine.machine import Machine
from spinn_machine.processor import Processor
from spinn_machine.sdram import SDRAM
from spinn_machine.link import Link
from spinn_machine.router import Router
from spinn_machine.chip import Chip


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


class NewPartitionerConstraint(AbstractPartitionerConstraint):

    def __init__(self, label):
        AbstractPartitionerConstraint.__init__(self, label)

    def is_constraint(self):
        return True

    def is_partitioner_constraint(self):
        """ Determine if this is a partitioner constraint
        """
        return True


class TestBasicPartitioner(unittest.TestCase):
    def setUp(self):
        self.vert1 = Vertex(10, "New AbstractConstrainedVertex 1")
        self.vert2 = Vertex(5, "New AbstractConstrainedVertex 2")
        self.vert3 = Vertex(3, "New AbstractConstrainedVertex 3")
        self.edge1 = PartitionableEdge(self.vert1, self.vert2, "First edge")
        self.edge2 = PartitionableEdge(self.vert2, self.vert1, "Second edge")
        self.edge3 = PartitionableEdge(self.vert1, self.vert3, "Third edge")
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
        self.bp = BasicPartitioner(1, 600)

    def test_new_basic_partitioner(self):
        self.assertEqual(self.bp._machine_time_step, 1)
        self.assertEqual(self.bp._runtime_in_machine_time_steps, 600)

    def test_partition_with_no_additional_constraints(self):
        self.assertEqual(self.vert1._model_based_max_atoms_per_core, 256)
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
        self.assertEqual(len(subgraph.subvertices), 3)
        vert_sizes = []
        for vert in self.verts:
            vert_sizes.append(vert.n_atoms)
        self.assertEqual(len(subgraph.subedges), 3)
        for subvert in subgraph.subvertices:
            self.assertIn(subvert.n_atoms, vert_sizes)

    def test_partition_with_no_additional_constraints_extra_edge(self):
        self.graph.add_edge(PartitionableEdge(self.vert3, self.vert1, "Extra edge"))
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
        self.assertEqual(len(subgraph.subvertices), 3)
        self.assertEqual(len(subgraph.subedges), 4)

    def test_partition_on_large_vertex_than_has_to_be_split(self):
        large_vertex = Vertex(300, "Large vertex")
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = PartitionableGraph("Graph with large vertex",
                           [large_vertex],
                           [])
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(subgraph.subvertices), 1)
        for subv in subgraph.subvertices:
            print subv.n_atoms, subv.label

    def test_partition_on_very_large_vertex_than_has_to_be_split(self):
        large_vertex = Vertex(500, "Large vertex")
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = PartitionableGraph("Graph with large vertex",
                           [large_vertex],
                           [])
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(subgraph.subvertices), 1)
        for subv in subgraph.subvertices:
            print subv.n_atoms, subv.label

    def test_partition_on_target_size_vertex_than_has_to_be_split(self):
        large_vertex = Vertex(1000, "Large vertex")
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = PartitionableGraph("Graph with large vertex",
                           [large_vertex],
                           [])
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
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
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
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
        with self.assertRaises(PacmanPartitionException):
            self.bp.partition(self.graph,self.machine)

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
        subgraph, mapper = self.bp.partition(self.graph,self.machine)

    def test_partition_with_more_sdram_than_default(self):
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(128*(2**21))

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
        subgraph, mapper = self.bp.partition(self.graph,self.machine)

    def test_partition_with_unsupported_constraints(self):
        with self.assertRaises(PacmanInvalidParameterException):
            constrained_vertex = Vertex(13, "Constrained")
            constrained_vertex.add_constraint(
                NewPartitionerConstraint("Mock constraint"))
            self.graph.add_vertex(constrained_vertex)
            partitioner = BasicPartitioner(1, 1000)
            subgraph, graph_to_sub_graph_mapper = \
                    partitioner.partition(self.graph, self.machine)

    def test_partition_with_empty_graph(self):
        self.graph = PartitionableGraph()
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
        self.assertEqual(len(subgraph.subvertices), 0)



if __name__ == '__main__':
    unittest.main()
