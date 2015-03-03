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
from pacman.utilities.progress_bar import ProgressBar
from pacman.utilities import utility_calls
from pacman.exceptions import PacmanPartitionException

import logging
from pacman.utilities.resource_tracker import ResourceTracker

logger = logging.getLogger(__name__)


class BasicPartitioner(AbstractPartitionAlgorithm):
    """ An basic algorithm that can partition a partitionable_graph based
        on the number of atoms in the vertices.
    """

    def __init__(self):
        """
        """
        AbstractPartitionAlgorithm.__init__(self)
        self._supported_constraints.append(PartitionerMaximumSizeConstraint)

    def _get_ratio(self, top, bottom):
        if bottom == 0:
            return 1.0
        return top / bottom

    # inherited from AbstractPartitionAlgorithm
    def partition(self, graph, machine):
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=graph.vertices,
            supported_constraints=self._supported_constraints,
            abstract_constraint_type=AbstractPartitionerConstraint)

        # start progress bar
        progress_bar = ProgressBar(len(graph.vertices),
                                   "on partitioning the partitionable_graph's"
                                   " vertices")
        vertices = graph.vertices
        subgraph = PartitionedGraph(label="partitioned_graph for partitionable"
                                          "_graph {}".format(graph.label))
        graph_to_subgraph_mapper = GraphMapper(graph.label, subgraph.label)
        resource_tracker = ResourceTracker(machine)

        # Partition one vertex at a time
        for vertex in vertices:

            # Get the usage of the first atom, then assume that this
            # will be the usage of all the atoms
            requirements = vertex.get_resources_used_by_atoms(0, 1, graph)

            # Locate the maximum resources available
            max_resources_available = \
                resource_tracker.get_maximum_constrained_resources_available(
                    vertex.constraints)

            # Find the ratio of each of the resources - if 0 is required,
            # assume the ratio is the max available
            atoms_per_sdram = self._get_ratio(
                max_resources_available.sdram.get_value(),
                requirements.sdram.get_value())
            atoms_per_dtcm = self._get_ratio(
                max_resources_available.dtcm.get_value(),
                requirements.dtcm.get_value())
            atoms_per_cpu = self._get_ratio(
                max_resources_available.cpu.get_value(),
                requirements.cpu.get_value())

            max_atom_values = [atoms_per_sdram, atoms_per_dtcm, atoms_per_cpu]

            max_atoms_constraints = utility_calls.locate_constraints_of_type(
                vertex.constraints, PartitionerMaximumSizeConstraint)
            for max_atom_constraint in max_atoms_constraints:
                max_atom_values.append(max_atom_constraint.size)

            atoms_per_core = min(max_atom_values)

            # Partition into subvertices
            counted = 0
            while counted < vertex.n_atoms:

                # Determine subvertex size
                remaining = vertex.n_atoms - counted
                if remaining > atoms_per_core:
                    alloc = atoms_per_core
                else:
                    alloc = remaining

                # Create and store new subvertex, and increment elements
                #  counted
                if counted < 0 or counted + alloc - 1 < 0:
                    raise PacmanPartitionException("Not enough resources"
                                                   " available to create"
                                                   " subvertex")

                vertex_slice = Slice(counted, alloc - 1)
                subvertex_usage = vertex.get_resources_used_by_atoms(
                    vertex_slice, graph)

                subvert = vertex.create_subvertex(
                    vertex_slice, subvertex_usage,
                    "{}:{}:{}".format(vertex.label, counted, alloc - 1),
                    self._get_remaining_constraints(vertex))
                subgraph.add_subvertex(subvert)
                graph_to_subgraph_mapper.add_subvertex(
                    subvert, counted, counted + alloc - 1, vertex)
                counted = counted + alloc

                # update allocated resources
                resource_tracker.allocate_constrained_resources(
                    subvertex_usage, vertex.constraints)

            # update and end progress bars as needed
            progress_bar.update()
        progress_bar.end()

        self._generate_sub_edges(subgraph, graph_to_subgraph_mapper, graph)

        return subgraph, graph_to_subgraph_mapper
