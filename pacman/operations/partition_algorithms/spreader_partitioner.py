"""
SpreaderPartitioner
"""

# constraints
from pacman.model.constraints.abstract_constraints.\
    abstract_partitioner_constraint import AbstractPartitionerConstraint
from pacman.model.constraints.partitioner_constraints.\
    partitioner_maximum_size_constraint import \
    PartitionerMaximumSizeConstraint
from pacman.model.constraints.partitioner_constraints.\
    partitioner_same_size_as_vertex_constraint \
    import PartitionerSameSizeAsVertexConstraint
from pacman.model.constraints.placer_constraints.\
    placer_chip_and_core_constraint\
    import PlacerChipAndCoreConstraint
from pacman.utilities.algorithm_utilities import partition_algorithm_utilities

# objects
from pacman.model.graph_mapper.graph_mapper import GraphMapper
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.model.graph_mapper.slice import Slice

# extras
from pacman import exceptions
from pacman.utilities import utility_calls
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker
from pacman.utilities.utility_objs.progress_bar import ProgressBar

import math
import logging
import sys

logger = logging.getLogger(__name__)


class SpreaderPartitioner(object):
    """ An basic algorithm that can partition a partitionable_graph based
    on atoms
    """

    # inherited from AbstractPartitionAlgorithm
    def __call__(self, graph, machine):
        """ Partition a partitionable_graph so that each
        subvertex will fit on a processor within the machine

        :param graph: The partitionable_graph to partition
        :type graph: :py:class:`pacman.model.graph.partitionable_graph.
        PartitionableGraph`
        :param machine: The machine with respect to which to partition the
        partitionable_graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :return: A partitioned_graph of partitioned vertices and edges from
        the partitionable_graph
        :rtype: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :raise pacman.exceptions.PacmanPartitionException: If something\
                   goes wrong with the partitioning
        """

        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=graph.vertices,
            abstract_constraint_type=AbstractPartitionerConstraint,
            supported_constraints=[PartitionerMaximumSizeConstraint,
                                   PartitionerSameSizeAsVertexConstraint,
                                   PlacerChipAndCoreConstraint])

        logger.info("* Running Spread Partitioner *")

        # Load the machine and vertices objects from the dao
        vertices = graph.vertices
        subgraph = PartitionedGraph(
            label="partitioned graph for {}".format(graph.label))

        graph_mapper = GraphMapper(graph.label, subgraph.label)
        resource_allocation = ResourceTracker(machine)

        core_constrained_vertices, chip_constrained_vertices, \
            not_constrained_vertices = \
            self._locate_placement_constrained_vertices(vertices)
        done_vertices = list()

        self._partition_vertices_on_specific_core(
            core_constrained_vertices, graph_mapper, graph, subgraph,
            done_vertices, resource_allocation)
        self._partition_a_vertex_specific_chip(
            chip_constrained_vertices, graph_mapper, graph, subgraph,
            done_vertices, resource_allocation)
        self._partition_none_constrained(
            not_constrained_vertices, graph_mapper, graph, subgraph,
            done_vertices, resource_allocation)

        partition_algorithm_utilities.generate_sub_edges(
            subgraph, graph_mapper, graph)

        results = dict()
        results['partitioned_graph'] = subgraph
        results['graph_mapper'] = graph_mapper
        return results

    def _partition_vertices_on_specific_core(
            self, core_constrained_vertices, graph_mapper, graph, subgraph,
            done_vertices, resource_allocation):
        """ takes vertices which need to be on a specific core and checks if
        they can be placed on them. otherwise raises an error

        :param core_constrained_vertices:
        :param graph_mapper:
        :param graph:
        :param subgraph:
        :param done_vertices:
        :return:
        """
        progress_bar = ProgressBar(
            len(core_constrained_vertices),
            "Partitioning vertices which require their own cores")

        for vertex in core_constrained_vertices:
            max_atom_constraint = \
                utility_calls.locate_constraints_of_type(
                    vertex.get_constraints(), PartitionerMaximumSizeConstraint)
            max_atoms = self._locate_min(max_atom_constraint)
            if vertex.atoms > max_atoms:
                raise exceptions.PacmanPartitionException(
                    "this vertex cannot be placed / partitioned because the "
                    "max_atom constraint is less than the number of neurons"
                    "which would require multiple cores, yet you have "
                    "requested a specific core to run the entire vertex."
                    "Please adjust your constraints and try again")
            else:
                vertex_slice = Slice(0, vertex.atoms - 1)
                resources = \
                    vertex.get_resources_used_by_atoms(vertex_slice, graph)
                subvertex = vertex.create_subvertex(
                    vertex_slice=vertex_slice,
                    resources_required=resources,
                    label="partitioned vertex with atoms {} to {} for vertex {}"
                          .format(vertex_slice.lo_atom, vertex_slice.hi_atom,
                                  vertex.label),
                    constraints=vertex.constraints)
                subgraph.add_subvertex(subvertex)
                graph_mapper.add_subvertex(subvertex, vertex_slice, vertex)
                done_vertices.append(vertex)
                resource_allocation.allocate_resources(
                    resources, vertex.get_constraints())
            progress_bar.update()
        progress_bar.end()

    def _partition_a_vertex_specific_chip(
            self, chip_constrained_vertices, graph_mapper, graph, subgraph,
            done_vertices, resource_allocation):
        """

        :param chip_constrained_vertices:
        :param graph_mapper:
        :param graph:
        :param subgraph:
        :param done_vertices:
        :return:
        """
        progress_bar = ProgressBar(
            len(chip_constrained_vertices),
            "Partitioning vertices which require their own chips")

        for vertex in chip_constrained_vertices.keys():
            if vertex not in done_vertices:
                vertex_constraint = chip_constrained_vertices[vertex]
                other_vertices_for_chip = list()
                other_vertices_for_chip.append(vertex)
                # locate other vertices which need to reside on the same chip.
                for other_vertex in chip_constrained_vertices.keys():
                    other_constraint = chip_constrained_vertices[other_vertex]
                    if (vertex != other_vertex and
                            other_constraint.x == vertex_constraint.x and
                            other_constraint.y == vertex_constraint.y and
                            other_vertex not in done_vertices):
                        other_vertices_for_chip.append(other_vertex)

                total_free_processors_on_chip = resource_allocation.\
                    total_free_processors_on_chip(vertex_constraint.x,
                                                  vertex_constraint.y)

                if (len(other_vertices_for_chip) >
                        total_free_processors_on_chip):
                    raise exceptions.PacmanElementAllocationException(
                        "Cannot allocate {} vertices on chip {},{} as it only"
                        " has {} cores available".format(
                            len(other_vertices_for_chip),
                            vertex_constraint.x, vertex_constraint.y,
                            total_free_processors_on_chip))

                # deduce min max
                min_max = self._determine_min_max_atoms(
                    other_vertices_for_chip, done_vertices)
                total_atoms = 0
                for current_vertex in other_vertices_for_chip:
                    if current_vertex not in done_vertices:
                        total_atoms += current_vertex.atoms
                min_per_core = \
                    math.ceil(total_atoms / total_free_processors_on_chip)

                # check can allocate atoms to fit user constraints
                if min_max <= min_per_core:
                    raise exceptions.PacmanElementAllocationException(
                        "Cannot split {} vertices over {} cores as the max "
                        "atoms per core is set to {} whereas the spread"
                        " expects to put {} per core.".format(
                            len(other_vertices_for_chip),
                            total_free_processors_on_chip, min_max,
                            min_per_core))
                for current_vertex in other_vertices_for_chip:
                    self._deal_with_none_constrained_vertices(
                        current_vertex, done_vertices, min_max,
                        graph, subgraph, graph_mapper, resource_allocation)
                progress_bar.update()
        progress_bar.end()

    @staticmethod
    def _locate_placement_constrained_vertices(vertices):
        """
        helper method which locates methods with a placement constraint.
        :param vertices: the partitionable graphs vertices
        :return: 4 lists where the first is vertices which are constrained to
        a processor and the second is constrained to a chip, 3rd is ones which
        need to be placed on the same chip as others and last is not constrained
        """
        none_constrained = list()
        chip_with_processors = dict()
        chip_constrained = dict()
        for vertex in vertices:
            placement_constraints = utility_calls.locate_constraints_of_type(
                vertex.constraints, PlacerChipAndCoreConstraint)
            if len(placement_constraints) == 0:
                none_constrained.append(vertex)
            else:
                for constraint in placement_constraints:
                    if isinstance(constraint, PlacerChipAndCoreConstraint):
                        if constraint.p is not None:
                            chip_with_processors[vertex] = constraint
                        else:
                            chip_constrained[vertex] = constraint
        return chip_with_processors, chip_constrained, none_constrained

    def _partition_none_constrained(
            self, not_constrained_vertices, graph_mapper, graph, subgraph,
            done_vertices, resource_allocation):
        """

        :param not_constrained_vertices:
        :param graph_mapper:
        :param graph:
        :param subgraph:
        :param done_vertices:
        :return:
        """
        free_processors = resource_allocation.total_free_processors()
        min_max = self._determine_min_max_atoms(not_constrained_vertices,
                                                done_vertices)
        total_atoms = 0
        for vertex in not_constrained_vertices:
            if vertex not in done_vertices:
                total_atoms += vertex.n_atoms
        min_per_core = int(math.ceil(float(total_atoms) /
                                      float(free_processors)))
        if min_per_core == 1:
            min_per_core = 0

        if min_max > min_per_core:
            progress_bar = ProgressBar(
                total_atoms,
                "Partitioning vertices which have no constraints")
            for vertex in not_constrained_vertices:
                self._deal_with_none_constrained_vertices(
                    vertex, done_vertices, min_per_core, graph, subgraph,
                    graph_mapper, resource_allocation, progress_bar)
            progress_bar.end()
        else:
            raise exceptions.PacmanElementAllocationException(
                "Cannot partition {} vertices, as they demand a max atom of {}"
                " whereas given the resources available, I can only spread "
                "them to {} per core".format(
                    not_constrained_vertices, min_max, min_per_core))

    @staticmethod
    def _locate_min(constraints):
        """

        :param constraints:
        :return:
        """
        min_value = None
        for constraint in constraints:
            if min_value is None:
                min_value = constraint.size
            else:
                if min_value >= constraint.size:
                    min_value = constraint.size
        return min_value

    @staticmethod
    def _deal_with_none_constrained_vertices(
            vertex, done_vertices, min_per_core, graph, subgraph, graph_mapper,
            resource_allocation, progress_bar):
        """

        :param vertex:
        :param done_vertices:
        :param min_per_core:
        :param graph:
        :param subgraph:
        :param graph_mapper:
        :return:
        """
        if vertex not in done_vertices:
            total_atoms = 0
            while total_atoms <= vertex.n_atoms - 1:
                if total_atoms + min_per_core > vertex.n_atoms - 1:
                    vertex_slice = Slice(
                        total_atoms,
                        total_atoms + (vertex.n_atoms - 1 - total_atoms))
                else:
                    vertex_slice = Slice(total_atoms,
                                         total_atoms + min_per_core)
                resources_used = \
                    vertex.get_resources_used_by_atoms(vertex_slice, graph)
                subvertex = vertex.create_subvertex(
                    vertex_slice=vertex_slice,
                    resources_required=resources_used,
                    label="partitioned vertex with atoms {} to "
                          "{} for vertex {}".format(vertex_slice.lo_atom,
                                                    vertex_slice.hi_atom,
                                                    vertex.label),
                    constraints=vertex.constraints)
                subgraph.add_subvertex(subvertex)
                graph_mapper.add_subvertex(subvertex, vertex_slice, vertex)
                resource_allocation.allocate_resources(resources_used)
                if min_per_core == 0:
                    total_atoms += 1
                else:
                    total_atoms += min_per_core
                progress_bar.update(vertex_slice.n_atoms)
            done_vertices.append(vertex)

    def _determine_min_max_atoms(self, vertices, done_vertices):
        """ helper method to determine what the min max value is based on
        the vertex max constraint.

        :param vertices: the vertexes of the application
        :return: a min max int value.
        """
        min_max = sys.maxint
        for vertex in vertices:
            if vertex not in done_vertices:
                constraints = vertex.constraints
                max_constraints = utility_calls.locate_constraints_of_type(
                    constraints, PartitionerMaximumSizeConstraint)
                max_values = list()
                for constraint in max_constraints:
                    max_values.append(constraint.size)
                vertex_min = self._locate_min(max_constraints)
                min_max = min(min_max, vertex_min)
        return min_max
