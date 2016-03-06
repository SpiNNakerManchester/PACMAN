import logging

from pacman.model.constraints.abstract_constraints.\
    abstract_partitioner_constraint import \
    AbstractPartitionerConstraint
from pacman.model.constraints.partitioner_constraints.\
    partitioner_same_size_as_vertex_constraint \
    import PartitionerSameSizeAsVertexConstraint
from pacman.model.graph_mapper.graph_mapper import \
    GraphMapper
from pacman.utilities.algorithm_utilities import partition_algorithm_utilities
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.model.constraints.partitioner_constraints.\
    partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from pacman.model.graph_mapper.slice import Slice
from pacman.utilities.utility_objs.progress_bar import ProgressBar
from pacman import exceptions
from pacman.utilities import utility_calls
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker

logger = logging.getLogger(__name__)


class PartitionAndPlacePartitioner(object):
    """  A partitioner that tries to ensure that SDRAM is not overloaded by\
         keeping track of the SDRAM usage on the various chips

    """

    # inherited from AbstractPartitionAlgorithm
    def __call__(self, graph, machine):
        """ Partition a partitionable_graph so that each subvertex will fit\
            on a processor within the machine

        :param graph: The partitionable_graph to partition
        :type graph:\
                    :py:class:`pacman.model.graph.partitionable_graph.PartitionableGraph`
        :param machine: The machine with respect to which to partition the\
                    partitionable_graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :return: A partitioned_graph of partitioned vertices and partitioned\
                    edges
        :rtype:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_graph.PartitionedGraph`
        :raise pacman.exceptions.PacmanPartitionException: If something\
                   goes wrong with the partitioning
        """
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=graph.vertices,
            abstract_constraint_type=AbstractPartitionerConstraint,
            supported_constraints=[PartitionerMaximumSizeConstraint,
                                   PartitionerSameSizeAsVertexConstraint])

        # Load the vertices and create the subgraph to fill
        vertices = graph.vertices
        subgraph = PartitionedGraph(
            label="partitioned graph for {}".format(graph.label))
        graph_mapper = GraphMapper(graph.label, subgraph.label)

        # sort out vertex's by constraints
        vertices = utility_calls.sort_objects_by_constraint_authority(vertices)

        # Set up the progress
        n_atoms = 0
        for vertex in vertices:
            n_atoms += vertex.n_atoms
        progress_bar = ProgressBar(n_atoms, "Partitioning graph vertices")

        resource_tracker = ResourceTracker(machine)

        # Partition one vertex at a time
        for vertex in vertices:

            # check that the vertex hasn't already been partitioned
            subverts_from_vertex = \
                graph_mapper.get_subvertices_from_vertex(vertex)

            # if not, partition
            if subverts_from_vertex is None:
                self._partition_vertex(
                    vertex, subgraph, graph_mapper, resource_tracker, graph)
            progress_bar.update(vertex.n_atoms)
        progress_bar.end()

        partition_algorithm_utilities.generate_sub_edges(
            subgraph, graph_mapper, graph)

        results = dict()
        results['partitioned_graph'] = subgraph
        results['graph_mapper'] = graph_mapper
        return results

    def _partition_vertex(
            self, vertex, subgraph, graph_to_subgraph_mapper, resource_tracker,
            graph):
        """ Partition a single vertex

        :param vertex: the vertex to partition
        :type vertex:\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :param subgraph: the partitioned_graph to add subverts to
        :type subgraph:\
                    py:class:`pacman.model.partitioned_graph.partitioned_graph.Subgraph`
        :param graph_to_subgraph_mapper: the mappings object from\
                    partitionable_graph to partitioned_graph which needs to be\
                    updated with new subverts
        :type graph_to_subgraph_mapper:\
                    py:class:'pacman.modelgraph_subgraph_mapper.graph_mapper.GraphMapper'
        :param resource_tracker: A tracker of assigned resources
        :type resource_tracker:\
                    :py:class:`pacman.utilities.resource_tracker.ResourceTracker`
        :param graph: the partitionable_graph object
        :type graph:\
                    :py:class:`pacman.model.graph.partitionable_graph.PartitionableGraph`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanPartitionException: if the extra vertex\
                    for partitioning identically has a different number of\
                    atoms than its counterpart.
        """

        partiton_together_vertices = \
            self._locate_vertices_to_partition_now(vertex)

        # locate max atoms per core
        possible_max_atoms = list()
        possible_max_atoms.append(vertex.get_max_atoms_per_core())

        for other_partitionable_vertex in partiton_together_vertices:
            max_atom_constraints =\
                utility_calls.locate_constraints_of_type(
                    other_partitionable_vertex.constraints,
                    PartitionerMaximumSizeConstraint)
            for constraint in max_atom_constraints:
                possible_max_atoms.append(constraint.size)
        max_atoms_per_core = min(possible_max_atoms)

        # partition by atoms
        self._partition_by_atoms(
            partiton_together_vertices, vertex.n_atoms, max_atoms_per_core,
            subgraph, graph, graph_to_subgraph_mapper, resource_tracker)

    def _partition_by_atoms(
            self, vertices, n_atoms, max_atoms_per_core, subgraph, graph,
            graph_to_subgraph_mapper, resource_tracker):
        """ Try to partition subvertices on how many atoms it can fit on\
            each subvert

        :param vertices: the vertexes that need to be partitioned at the same \
                    time
        :type vertices: iterable list of\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :param n_atoms: the atoms of the first vertex
        :type n_atoms: int
        :param max_atoms_per_core: the max atoms from all the vertexes\
                    considered that have max_atom constraints
        :type max_atoms_per_core: int
        :param subgraph: the partitioned_graph of the problem space to put\
                    subverts in
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param graph: the partitionable_graph object
        :type graph:\
                    :py:class:`pacman.model.partitionable_graph.partitionable_graph.PartitionableGraph`
        :param graph_to_subgraph_mapper: the mapper from\
                    partitionable_graph to partitioned_graph
        :type graph_to_subgraph_mapper:\
                    py:class:'pacman.modelgraph_subgraph_mapper.graph_mapper.GraphMapper'
        :param resource_tracker: A tracker of assigned resources
        :type resource_tracker:\
                    :py:class:`pacman.utilities.resource_tracker.ResourceTracker`
        :type no_machine_time_steps: int
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

            # Create the subvertices
            for (vertex, used_resources) in used_placements:
                vertex_slice = Slice(lo_atom, hi_atom)
                subvertex = vertex.create_subvertex(
                    vertex_slice, used_resources,
                    "{}:{}:{}".format(vertex.label, lo_atom, hi_atom),
                    partition_algorithm_utilities.get_remaining_constraints(
                        vertex))

                # update objects
                subgraph.add_subvertex(subvertex)
                graph_to_subgraph_mapper.add_subvertex(
                    subvertex, vertex_slice, vertex)

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
        :param graph: the partitionable graph used by the partitioner
        :type graph:
                    :py:class:`pacman.model.partitionable_graph.partitionable_graph.PartitionableGraph`
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
            new_resources = placed_vertex.get_resources_used_by_atoms(
                vertex_slice, graph)

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
        :param vertices: the vertexes that need to be partitioned at the same \
                    time
        :type vertices: iterable of\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :param max_atoms_per_core: the min max atoms from all the vertexes \
                    considered that have max_atom constraints
        :type max_atoms_per_core: int
        :param graph: the partitionable_graph object
        :type graph:\
                    :py:class:`pacman.model.graph.partitionable_graph.PartitionableGraph`
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

            # get max resources available on machine
            resources = \
                resource_tracker.get_maximum_constrained_resources_available(
                    vertex.constraints)

            # get resources used by vertex
            vertex_slice = Slice(lo_atom, hi_atom)
            used_resources = vertex.get_resources_used_by_atoms(
                vertex_slice, graph)

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
                    used_resources = vertex.get_resources_used_by_atoms(
                        vertex_slice, graph)
                    ratio = self._find_max_ratio(used_resources, resources)

            # If we couldn't partition, raise an exception
            if hi_atom < lo_atom:
                raise exceptions.PacmanPartitionException(
                    "No more of vertex {} would fit on the board:\n"
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
                used_placements.append(
                    (vertex, x, y, p, used_resources,
                     ip_tags, reverse_ip_tags))
            except exceptions.PacmanValueError as e:

                raise exceptions.PacmanValueError(
                    "Unable to allocate requested resources to"
                    " vertex {}:\n{}".format(vertex, e))

        # reduce data to what the parent requires
        final_placements = list()
        for (vertex, _, _, _, used_resources, _, _) in used_placements:
            final_placements.append((vertex, used_resources))

        return final_placements, min_hi_atom

    def _scale_up_resource_usage(
            self, used_resources, hi_atom, lo_atom, max_atoms_per_core, vertex,
            resources, ratio, graph):
        """ Try to push up the number of atoms in a subvertex to be as close\
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
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
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
            used_resources = vertex.get_resources_used_by_atoms(
                vertex_slice, graph)
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
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
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
        if (resources.cpu.get_value() == 0 or
                max_resources.cpu.get_value() == 0):
            cpu_ratio = 0
        else:
            cpu_ratio = (float(resources.cpu.get_value()) /
                         float(max_resources.cpu.get_value()))
        if (resources.dtcm.get_value() == 0 or
                max_resources.dtcm.get_value() == 0):
            dtcm_ratio = 0
        else:
            dtcm_ratio = (float(resources.dtcm.get_value()) /
                          float(max_resources.dtcm.get_value()))
        if (resources.sdram.get_value() == 0 or
                max_resources.sdram.get_value() == 0):
            sdram_ratio = 0
        else:
            sdram_ratio = (float(resources.sdram.get_value()) /
                           float(max_resources.sdram.get_value()))
        return max((cpu_ratio, dtcm_ratio, sdram_ratio))

    @staticmethod
    def _locate_vertices_to_partition_now(vertex):
        """ Locate any other vertices that need to be partitioned with the\
            exact same ranges of atoms

        :param vertex: the vertex that is currently being partitioned
        :type vertex:\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :return: iterable of vertexes that need to be partitioned with the\
                    exact same range of atoms
        :rtype: iterable of\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
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
            else:
                partition_together_vertices.append(constraint.vertex)
        return partition_together_vertices
