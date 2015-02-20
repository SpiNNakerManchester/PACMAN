from pacman.model.constraints.abstract_constraints.\
    abstract_partitioner_constraint import \
    AbstractPartitionerConstraint
from pacman.model.graph_mapper.graph_mapper import \
    GraphMapper
from pacman.model.graph_mapper.slice import Slice
from pacman.operations.abstract_algorithms.abstract_partition_algorithm\
    import AbstractPartitionAlgorithm
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.model.constraints.partitioner_constraints.\
    partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from spinn_machine.processor import Processor
from pacman.utilities.progress_bar import ProgressBar
from pacman.utilities import utility_calls
from pacman.exceptions import PacmanPartitionException

import logging

logger = logging.getLogger(__name__)


class BasicPartitioner(AbstractPartitionAlgorithm):
    """ An basic algorithm that can partition a partitionable_graph based
    on atoms
    """

    def __init__(self, machine_time_step, runtime_in_machine_time_steps):
        """constructor to build a
        pacman.operations.partition_algorithms.basic_partitioner.BasicPartitioner

        :param machine_time_step: the length of tiem in ms for a timer tick
        :param runtime_in_machine_time_steps: the number of timer ticks
        expected to occur due to the runtime
        :type machine_time_step: int
        :type runtime_in_machine_time_steps: long
        :return: a new
        pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm
        :rtype: pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm
        :raises None: does not raise any known expection
        """
        AbstractPartitionAlgorithm.__init__(self, machine_time_step,
                                            runtime_in_machine_time_steps)
        self._supported_constraints.append(PartitionerMaximumSizeConstraint)

    #inherited from AbstractPartitionAlgorithm
    def partition(self, graph, machine):
        """ Partition a partitionable_graph so that each
        subvertex will fit on a processor within the machine

        :param graph: The partitionable_graph to partition
        :type graph: :py:class:`pacman.model.graph.partitionable_graph.PartitionableGraph`
        :param machine: The machine with respect to which to partition the partitionable_graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :return: A partitioned_graph of partitioned vertices and edges from the partitionable_graph
        :rtype: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :raise pacman.exceptions.PacmanPartitionException: If something\
                   goes wrong with the partitioning
        """
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=graph.vertices,
            supported_constraints=self._supported_constraints,
            abstract_constraint_type=AbstractPartitionerConstraint)
        #start progress bar
        progress_bar = ProgressBar(len(graph.vertices),
                                   "on partitioning the partitionable_graph's"
                                   " vertices")
        vertices = graph.vertices
        subgraph = PartitionedGraph(label="partitioned_graph for partitionable"
                                          "_graph {}".format(graph.label))
        graph_to_subgraph_mapper = GraphMapper(graph.label, subgraph.label)
        # Partition one vertex at a time
        for vertex in vertices:
            # Compute atoms per core from resource availability
            requirements = \
                vertex.get_resources_used_by_atoms(0, 1, graph)

            #locate max SDRAM available. SDRAM is the only one that's changeable
            #during partitioning, as DTCM and cpu cycles are bespoke to a
            #processor.

            max_resources_available_on_processor = \
                self._get_maximum_resources_per_processor(vertex.constraints,
                                                          machine)
            if requirements.sdram.get_value() == 0:
                apc_sd = max_resources_available_on_processor
            else:
                apc_sd = max_resources_available_on_processor.sdram.get_value()\
                    / requirements.sdram.get_value()

            if requirements.dtcm.get_value() == 0:
                apc_dt = Processor.DTCM_AVAILABLE
            else:
                apc_dt =\
                    Processor.DTCM_AVAILABLE \
                    / requirements.dtcm.get_value()

            if requirements.cpu.get_value() == 0:
                apc_cp = Processor.CPU_AVAILABLE
            else:
                apc_cp = \
                    Processor.CPU_AVAILABLE \
                    / requirements.cpu.get_value()

            max_atom_values = [apc_sd, apc_dt, apc_cp]

            max_atoms_constraints = \
                utility_calls.locate_constraints_of_type(
                    vertex.constraints, PartitionerMaximumSizeConstraint)
            for max_atom_constraint in max_atoms_constraints:
                max_atom_values.append(max_atom_constraint.size)

            apc = min(max_atom_values)

            # Partition into subvertices
            counted = 0
            while counted < vertex.n_atoms:
                # Determine subvertex size
                remaining = vertex.n_atoms - counted
                if remaining > apc:
                    alloc = apc
                else:
                    alloc = remaining
                # Create and store new subvertex, and increment elements
                #  counted
                if counted < 0 or counted + alloc - 1 < 0:
                    raise PacmanPartitionException("Not enough resources"
                                                   " available to create"
                                                   " subvertex")
                subvertex_usage = \
                    vertex.get_resources_used_by_atoms(
                        counted, counted + alloc - 1, graph)

                vertex_slice = Slice(counted, alloc - 1)
                subvert = vertex.create_subvertex(
                    vertex_slice, subvertex_usage,
                    "subvertex with low atoms {} and hi atoms {} for vertex {}"
                    .format(counted, alloc - 1, vertex.label))
                subgraph.add_subvertex(subvert)
                graph_to_subgraph_mapper.add_subvertex(
                    subvert, counted, counted + alloc - 1, vertex)
                counted = counted + alloc

                #update sdram calc
                self._update_sdram_allocator(vertex, subvertex_usage, machine)
                self._add_vertex_constraints_to_subvertex(subvert, vertex)
            #update and end progress bars as needed
            progress_bar.update()
        progress_bar.end()

        self._generate_sub_edges(subgraph, graph_to_subgraph_mapper, graph)

        return subgraph, graph_to_subgraph_mapper