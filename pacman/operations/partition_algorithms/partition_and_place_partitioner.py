import logging
from pacman.model.abstract_classes.abstract_has_global_max_atoms import \
    AbstractHasGlobalMaxAtoms

from pacman.model.graphs.common.slice import Slice

from pacman import exceptions
from pacman.model.constraints.partitioner_constraints.\
    abstract_partitioner_constraint import \
    AbstractPartitionerConstraint
from pacman.model.constraints.partitioner_constraints.\
    partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from pacman.model.constraints.partitioner_constraints.\
    partitioner_same_size_as_vertex_constraint \
    import PartitionerSameSizeAsVertexConstraint
from pacman.model.graphs.common.graph_mapper import \
    GraphMapper
from pacman.model.graphs.machine.impl.machine_graph import MachineGraph
from pacman.utilities import utility_calls
from pacman.utilities.algorithm_utilities import partition_algorithm_utilities
from pacman.utilities.algorithm_utilities import placer_algorithm_utilities
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker
from spinn_machine.utilities.progress_bar import ProgressBar

logger = logging.getLogger(__name__)


class PartitionAndPlacePartitioner(object):
    """  A partitioner that tries to ensure that SDRAM is not overloaded by\
         keeping track of the SDRAM usage on the various chips

    """

    __slots__ = []

    # inherited from AbstractPartitionAlgorithm
    def __call__(self, graph, machine):
        """

        :param graph: The application_graph to partition
        :type graph:\
                    :py:class:`pacman.model.graph.application.application_graph.ApplicationGraph`
        :param machine: The machine with respect to which to partition the\
                    application_graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :return: A machine_graph of partitioned vertices and partitioned\
                    edges
        :rtype:\
                    :py:class:`pacman.model.graph.machine.machine_graph.MachineGraph`
        :raise pacman.exceptions.PacmanPartitionException: If something\
                   goes wrong with the partitioning
        """
        ResourceTracker.check_constraints(graph.vertices)
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=graph.vertices,
            abstract_constraint_type=AbstractPartitionerConstraint,
            supported_constraints=[PartitionerMaximumSizeConstraint,
                                   PartitionerSameSizeAsVertexConstraint])

        # Load the vertices and create the machine_graph to fill
        vertices = graph.vertices
        machine_graph = MachineGraph(
            label="partitioned graph for {}".format(graph.label))
        graph_mapper = GraphMapper()

        # sort out vertex's by placement constraints
        vertices = placer_algorithm_utilities\
            .sort_vertices_by_known_constraints(vertices)

        # Set up the progress
        n_atoms = 0
        for vertex in vertices:
            n_atoms += vertex.n_atoms
        progress_bar = ProgressBar(n_atoms, "Partitioning graph vertices")

        resource_tracker = ResourceTracker(machine)

        # Partition one vertex at a time
        for vertex in vertices:
            # check that the vertex hasn't already been partitioned
            machine_vertices = graph_mapper.get_machine_vertices(vertex)

            # if not, partition
            if machine_vertices is None:
                self._partition_vertex(
                    vertex, machine_graph, graph_mapper, resource_tracker,
                    graph, progress_bar)
        progress_bar.end()

        partition_algorithm_utilities.generate_machine_edges(
            machine_graph, graph_mapper, graph)

        return machine_graph, graph_mapper, len(resource_tracker.keys)

    def _partition_vertex(
            self, vertex, machine_graph, graph_mapper, resource_tracker,
            graph, progress_bar):
        """ Partition a single vertex

        :param vertex: the vertex to partition
        :type vertex:\
            :py:class:`pacman.model.graph.application.abstract_application_vertex.AbstractApplicationVertex`
        :param machine_graph: the graph to add vertices to
        :type machine_graph:\
            :py:class:`pacman.model.graph.machine.machine_graph.MachineGraph`
        :param graph_mapper: the mappings between graphs
        :type graph_mapper:\
            :py:class:'pacman.model.graph.graph_mapper.GraphMapper'
        :param resource_tracker: A tracker of assigned resources
        :type resource_tracker:\
            :py:class:`pacman.utilities.resource_tracker.ResourceTracker`
        :param graph: the graph object
        :type graph:\
            :py:class:`pacman.model.graph.application.application_graph.ApplicationGraph`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanPartitionException: if the extra vertex\
                    for partitioning identically has a different number of\
                    atoms than its counterpart.
        """

        partition_together_vertices = \
            self._locate_vertices_to_partition_now(vertex)

        # locate max atoms per core
        possible_max_atoms = list()
        if isinstance(vertex, AbstractHasGlobalMaxAtoms):
            possible_max_atoms.append(vertex.get_max_atoms_per_core())

        for other_vertex in partition_together_vertices:
            max_atom_constraints = utility_calls.locate_constraints_of_type(
                other_vertex.constraints,
                PartitionerMaximumSizeConstraint)
            for constraint in max_atom_constraints:
                possible_max_atoms.append(constraint.size)
        max_atoms_per_core = min(possible_max_atoms)

        # partition by atoms
        self._partition_by_atoms(
            partition_together_vertices, vertex.n_atoms, max_atoms_per_core,
            machine_graph, graph, graph_mapper, resource_tracker, progress_bar)

    def _partition_by_atoms(
            self, vertices, n_atoms, max_atoms_per_core, machine_graph, graph,
            graph_mapper, resource_tracker, progress_bar):
        """ Try to partition vertices on how many atoms it can fit on\
            each vertex

        :param vertices:\
            the vertexes that need to be partitioned at the same time
        :type vertices:\
            iterable list of\
            :py:class:`pacman.model.graph.application.abstract_application_vertex.AbstractApplicationVertex`
        :param n_atoms: the atoms of the first vertex
        :type n_atoms: int
        :param max_atoms_per_core:\
            the max atoms from all the vertexes considered that have max_atom\
            constraints
        :type max_atoms_per_core: int
        :param machine_graph: the machine graph
        :type machine_graph:\
            :py:class:`pacman.model.graph.machine.machine_graph.MachineGraph`
        :param graph: the application graph
        :type graph:\
            :py:class:`pacman.model.graph.application.application_graph.ApplicationGraph`
        :param graph_mapper: the mapper between graphs
        :type graph_mapper:\
            :py:class:'pacman.model.graph.graph_mapper.GraphMapper'
        :param resource_tracker: A tracker of assigned resources
        :type resource_tracker:\
            :py:class:`pacman.utilities.resource_tracker.ResourceTracker`
        """
        n_atoms_placed = 0
        while n_atoms_placed < n_atoms:

            lo_atom = n_atoms_placed
            hi_atom = lo_atom + max_atoms_per_core - 1
            if hi_atom >= n_atoms:
                hi_atom = n_atoms - 1

            # Scale down the number of atoms to fit the available resources
            used_placements, hi_atom = self._scale_down_resources(
                lo_atom, hi_atom, vertices, resource_tracker,
                max_atoms_per_core, graph)

            # Update where we are
            n_atoms_placed = hi_atom + 1

            # Create the vertices
            for (vertex, used_resources) in used_placements:
                vertex_slice = Slice(lo_atom, hi_atom)
                machine_vertex = vertex.create_machine_vertex(
                    vertex_slice, used_resources,
                    label="{}:{}:{}".format(vertex.label, lo_atom, hi_atom),
                    constraints=partition_algorithm_utilities
                        .get_remaining_constraints(vertex))

                # update objects
                machine_graph.add_vertex(machine_vertex)
                graph_mapper.add_vertex_mapping(
                    machine_vertex, vertex_slice, vertex)

            progress_bar.update(((hi_atom - lo_atom) + 1) * len(vertices))

    @staticmethod
    def _reallocate_resources(
            used_placements, resource_tracker, lo_atom, hi_atom, graph):
        """ readjusts resource allocation and updates the placement list to\
            take into account the new layout of the atoms

        :param used_placements: the original list of tuples containing\
                    placement data
        :type used_placements: iterable of tuples
        :param resource_tracker: the tracker of resources
        :type resource_tracker:\
                    :py:class:`pacman.utilities.resource_tracker.ResourceTracker`
        :param lo_atom: the low atom of a slice to be considered
        :type lo_atom: int
        :param hi_atom: the high atom of a slice to be considered
        :type hi_atom: int
        :param graph: the graph used by the partitioner
        :type graph:
                    :py:class:`pacman.model.graph.application.application_graph.ApplicationGraph`
        :return: the new list of tuples containing placement data
        :rtype: iterable of tuples
        """

        new_used_placements = list()
        for (placed_vertex, x, y, p, placed_resources,
                ip_tags, reverse_ip_tags) in used_placements:

            # Deallocate the existing resources
            resource_tracker.unallocate_resources(
                x, y, p, placed_resources, ip_tags, reverse_ip_tags)

            # Get the new resource usage
            vertex_slice = Slice(lo_atom, hi_atom)
            new_resources = \
                placed_vertex.get_resources_used_by_atoms(vertex_slice)

            # Re-allocate the existing resources
            (x, y, p, ip_tags, reverse_ip_tags) = \
                resource_tracker.allocate_constrained_resources(
                    new_resources, placed_vertex.constraints)
            new_used_placements.append(
                (placed_vertex, x, y, p, new_resources, ip_tags,
                 reverse_ip_tags))
        return new_used_placements

    # noinspection PyUnusedLocal
    def _scale_down_resources(
            self, lo_atom, hi_atom, vertices, resource_tracker,
            max_atoms_per_core, graph):
        """ Reduce the number of atoms on a core so that it fits within the
            resources available.

        :param lo_atom: the number of atoms already partitioned
        :type lo_atom: int
        :param hi_atom: the total number of atoms to place for this vertex
        :type hi_atom: int
        :param vertices:\
            the vertexes that need to be partitioned at the same time
        :type vertices:\
            iterable of\
            :py:class:`pacman.model.graph.application.abstract_application_vertex.AbstractApplicationVertex`
        :param max_atoms_per_core:\
            the max atoms from all the vertexes considered that have max_atom\
            constraints
        :type max_atoms_per_core: int
        :param graph: the application graph object
        :type graph:\
            :py:class:`pacman.model.graph.application.application_graph.ApplicationGraph`
        :param resource_tracker: Tracker of used resources
        :type resource_tracker: spinnmachine.machine.Machine object
        :return: the list of placements made by this method and the new amount\
                    of atoms partitioned
        :rtype: tuple of (iterable of tuples, int)
        :raise PacmanPartitionException: when the vertex cannot be partitioned
        """
        used_placements = list()

        # Find the number of atoms that will fit in each vertex given the
        # resources available
        min_hi_atom = hi_atom
        for i in range(len(vertices)):
            vertex = vertices[i]

            # get resources used by vertex
            vertex_slice = Slice(lo_atom, hi_atom)
            used_resources = vertex.get_resources_used_by_atoms(vertex_slice)

            # get max resources available on machine
            resources = \
                resource_tracker.get_maximum_constrained_resources_available(
                    used_resources, vertex.constraints)

            # Work out the ratio of used to available resources
            ratio = self._find_max_ratio(used_resources, resources)

            while ratio > 1.0 and hi_atom >= lo_atom:

                # Scale the resources by the ratio
                old_n_atoms = (hi_atom - lo_atom) + 1
                new_n_atoms = int(float(old_n_atoms) / (ratio * 1.1))

                # Avoid infinite looping
                if old_n_atoms == new_n_atoms:
                    new_n_atoms -= 1

                # Find the new resource usage
                hi_atom = lo_atom + new_n_atoms - 1
                if hi_atom >= lo_atom:
                    vertex_slice = Slice(lo_atom, hi_atom)
                    used_resources = \
                        vertex.get_resources_used_by_atoms(vertex_slice)
                    ratio = self._find_max_ratio(used_resources, resources)

            # If we couldn't partition, raise an exception
            if lo_atom < 1:
                raise exceptions.PacmanPartitionException(
                    "No vertex '{}' would fit on the board at all:\n"
                    "    Request for SDRAM: {}\n"
                    "    Largest SDRAM space: {}".format(
                        vertex,
                        used_resources.sdram.get_value(),
                        resources.sdram.get_value()))
            if hi_atom < lo_atom:
                raise exceptions.PacmanPartitionException(
                    "No more of vertex '{}' would fit on the board:\n"
                    "    Allocated so far: {} atoms\n"
                    "    Request for SDRAM: {}\n"
                    "    Largest SDRAM space: {}".format(
                        vertex, lo_atom - 1,
                        used_resources.sdram.get_value(),
                        resources.sdram.get_value()))

            # Try to scale up until just below the resource usage
            used_resources, hi_atom = self._scale_up_resource_usage(
                used_resources, hi_atom, lo_atom, max_atoms_per_core, vertex,
                resources, ratio, graph)

            # If this hi_atom is smaller than the current minimum, update the
            # other placements to use (hopefully) less resources
            if hi_atom < min_hi_atom:
                min_hi_atom = hi_atom
                used_placements = self._reallocate_resources(
                    used_placements, resource_tracker, lo_atom, hi_atom, graph)

            # Attempt to allocate the resources for this vertex on the machine
            try:
                (x, y, p, ip_tags, reverse_ip_tags) = \
                    resource_tracker.allocate_constrained_resources(
                        used_resources, vertex.constraints)
                used_placements.append((vertex, x, y, p, used_resources,
                     ip_tags, reverse_ip_tags))
            except exceptions.PacmanValueError as e:
                raise exceptions.PacmanValueError(
                    "Unable to allocate requested resources to"
                    " vertex '{}':\n{}".format(vertex, e))

        # reduce data to what the parent requires
        final_placements = list()
        for (vertex, _, _, _, used_resources, _, _) in used_placements:
            final_placements.append((vertex, used_resources))

        return final_placements, min_hi_atom

    def _scale_up_resource_usage(
            self, used_resources, hi_atom, lo_atom, max_atoms_per_core, vertex,
            resources, ratio, graph):
        """ Try to push up the number of atoms in a vertex to be as close\
            to the available resources as possible

        :param used_resources: the resources used by the machine so far
        :type used_resources:\
                    :py:class:`pacman.model.resources.resource.Resource`
        :param hi_atom: the total number of atoms to place for this vertex
        :type hi_atom: int
        :param lo_atom: the number of atoms already partitioned
        :type lo_atom: int
        :param max_atoms_per_core: the min max atoms from all the vertexes \
                    considered that have max_atom constraints
        :type max_atoms_per_core: int
        :param vertex: the vertexes to scale up the num atoms per core for
        :type vertex:\
                    :py:class:`pacman.model.graph.application.abstract_application_vertex.AbstractApplicationVertex`
        :param resources: the resource estimate for the vertex for a given\
                    number of atoms
        :type resources:\
                    :py:class:`pacman.model.resources.resource.Resource`
        :param ratio: the ratio between max atoms and available resources
        :type ratio: int
        :return: the new resources used and the new hi_atom
        :rtype: tuple of\
                    (:py:class:`pacman.model.resources.resource.Resource`,\
                    int)
        """

        previous_used_resources = used_resources
        previous_hi_atom = hi_atom

        # Keep searching while the ratio is still in range,
        # the next hi_atom value is still less than the number of atoms,
        # and the number of atoms is less than the constrained number of atoms
        while ((ratio < 1.0) and ((hi_atom + 1) < vertex.n_atoms) and
                ((hi_atom - lo_atom + 2) < max_atoms_per_core)):

            # Update the hi_atom, keeping track of the last hi_atom which
            # resulted in a ratio < 1.0
            previous_hi_atom = hi_atom
            hi_atom += 1

            # Find the new resource usage, keeping track of the last usage
            # which resulted in a ratio < 1.0
            previous_used_resources = used_resources
            vertex_slice = Slice(lo_atom, hi_atom)
            used_resources = vertex.get_resources_used_by_atoms(vertex_slice)
            ratio = self._find_max_ratio(used_resources, resources)

        # If we have managed to fit everything exactly (unlikely but possible),
        # return the matched resources and high atom count
        if ratio == 1.0:
            return used_resources, hi_atom

        # At this point, the ratio > 1.0, so pick the last allocation of
        # resources, which will be < 1.0
        return previous_used_resources, previous_hi_atom

    @staticmethod
    def _get_max_atoms_per_core(vertices):
        """ Find the max atoms per core for a collection of vertices

        :param vertices: a iterable list of vertices
        :type vertices: iterable of\
                    :py:class:`pacman.model.graph.application.abstract_application_vertex.AbstractApplicationVertex`
        :return: the minimum level of max atoms from all constraints
        :rtype: int
        :raise None: this method does not raise any known exceptions
        """
        max_atoms_per_core = 0
        for v in vertices:
            max_for_vertex = v.get_maximum_atoms_per_core()

            # If there is no maximum, the maximum is the number of atoms
            if max_for_vertex is None:
                max_for_vertex = v.atoms

            # Override the maximum with any custom maximum
            if v.custom_max_atoms_per_core is not None:
                max_for_vertex = v.custom_max_atoms_per_core

            max_atoms_per_core = max(max_atoms_per_core, max_for_vertex)
        return max_atoms_per_core

    @staticmethod
    def _ratio(a, b):
        """Get the ratio between two resource descriptors, with special
        handling for when either descriptor is zero.
        """
        aval = a.get_value()
        bval = b.get_value()
        if aval == 0 or bval == 0:
            return 0
        return float(aval) / float(bval)

    @staticmethod
    def _find_max_ratio(resources, max_resources):
        """ Find the max ratio between the resources

        :param resources: the resources used by the vertex
        :type resources:\
                    :py:class:`pacman.model.resources.resource_container.ResourceContainer`
        :param max_resources: the max resources available from the machine
        :type max_resources: \
                    :py:class:`pacman.model.resources.resource_container.ResourceContainer`
        :return: the largest ratio of resources
        :rtype: int
        :raise None: this method does not raise any known exceptions

        """
        cpu_ratio = PartitionAndPlacePartitioner._ratio(
            resources.cpu_cycles, max_resources.cpu_cycles)
        dtcm_ratio = PartitionAndPlacePartitioner._ratio(
            resources.dtcm, max_resources.dtcm)
        sdram_ratio = PartitionAndPlacePartitioner._ratio(
            resources.sdram, max_resources.sdram)
        return max((cpu_ratio, dtcm_ratio, sdram_ratio))

    @staticmethod
    def _locate_vertices_to_partition_now(vertex):
        """ Locate any other vertices that need to be partitioned with the\
            exact same ranges of atoms

        :param vertex: the vertex that is currently being partitioned
        :type vertex:\
                    :py:class:`pacman.model.graph.application.abstract_application_vertex.AbstractApplicationVertex`
        :return: iterable of vertexes that need to be partitioned with the\
                    exact same range of atoms
        :rtype: iterable of\
                    :py:class:`pacman.model.graph.application.abstract_application_vertex.AbstractApplicationVertex`
        :raise PacmanPartitionException: if the vertices that need to be \
                    partitioned the same have different numbers of atoms
        """
        partition_together_vertices = list()
        partition_together_vertices.append(vertex)
        same_size_vertex_constraints = \
            utility_calls.locate_constraints_of_type(
                vertex.constraints, PartitionerSameSizeAsVertexConstraint)
        for constraint in same_size_vertex_constraints:
            if constraint.vertex.n_atoms != vertex.n_atoms:
                raise exceptions.PacmanPartitionException(
                    "A vertex and its partition-dependent vertices must "
                    "have the same number of atoms")
            partition_together_vertices.append(constraint.vertex)
        return partition_together_vertices
