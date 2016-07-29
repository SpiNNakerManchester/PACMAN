import logging

from pacman.model.graphs.common.slice import Slice

from pacman.exceptions import PacmanPartitionException
from pacman.model.constraints.partitioner_constraints.\
    abstract_partitioner_constraint import AbstractPartitionerConstraint
from pacman.model.constraints.partitioner_constraints.\
    partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from pacman.model.graphs.common.graph_mapper import GraphMapper
from pacman.model.graphs.machine.impl.machine_graph import MachineGraph
from pacman.utilities import utility_calls
from pacman.utilities.algorithm_utilities import partition_algorithm_utilities
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker
from spinn_machine.utilities.progress_bar import ProgressBar

logger = logging.getLogger(__name__)


class BasicPartitioner(object):
    """ An basic algorithm that can partition an application graph based\
        on the number of atoms in the vertices.
    """

    @staticmethod
    def _get_ratio(top, bottom):
        if bottom == 0:
            return 1.0
        return top / bottom

    # inherited from AbstractPartitionAlgorithm
    def __call__(self, graph, machine):
        """

        :param graph: The application_graph to partition
        :type graph:\
            :py:class:`pacman.model.graph.application.application_graph.ApplicationGraph`
        :param machine:\
            The machine with respect to which to partition the application\
            graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :return: A machine graph
        :rtype:\
            :py:class:`pacman.model.graph.machine.machine_graph.MachineGraph`
        :raise pacman.exceptions.PacmanPartitionException:\
            If something goes wrong with the partitioning
        """
        ResourceTracker.check_constraints(graph.vertices)
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=graph.vertices,
            supported_constraints=[PartitionerMaximumSizeConstraint],
            abstract_constraint_type=AbstractPartitionerConstraint)

        # start progress bar
        progress_bar = ProgressBar(len(graph.vertices),
                                   "Partitioning graph vertices")
        vertices = graph.vertices
        machine_graph = MachineGraph(
            "Machine graph for {}".format(graph.label))
        graph_mapper = GraphMapper()
        resource_tracker = ResourceTracker(machine)

        # Partition one vertex at a time
        for vertex in vertices:

            # Get the usage of the first atom, then assume that this
            # will be the usage of all the atoms
            requirements = vertex.get_resources_used_by_atoms(Slice(0, 1))

            # Locate the maximum resources available
            max_resources_available = \
                resource_tracker.get_maximum_constrained_resources_available(
                    vertex)

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

            # Partition into vertices
            counted = 0
            while counted < vertex.n_atoms:

                # Determine vertex size
                remaining = vertex.n_atoms - counted
                if remaining > atoms_per_core:
                    alloc = atoms_per_core
                else:
                    alloc = remaining

                # Create and store new vertex, and increment elements
                #  counted
                if counted < 0 or counted + alloc - 1 < 0:
                    raise PacmanPartitionException(
                        "Not enough resources available to create vertex")

                vertex_slice = Slice(counted, counted + (alloc - 1))
                resources = vertex.get_resources_used_by_atoms(vertex_slice)

                machine_vertex = vertex.create_machine_vertex(
                    vertex_slice, resources,
                    "{}:{}:{}".format(vertex.label, counted,
                                      (counted + (alloc - 1))),
                    partition_algorithm_utilities.
                    get_remaining_constraints(vertex))
                machine_graph.add_vertex(machine_vertex)
                graph_mapper.add_vertex_mapping(
                    machine_vertex, vertex_slice, vertex)
                counted = counted + alloc

                # update allocated resources
                resource_tracker.allocate_constrained_resources(
                    resources, vertex)

            # update and end progress bars as needed
            progress_bar.update()
        progress_bar.end()

        partition_algorithm_utilities.generate_machine_edges(
            machine_graph, graph_mapper, graph)

        return machine_graph, graph_mapper, len(resource_tracker.keys)
