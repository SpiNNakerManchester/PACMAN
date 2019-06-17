from __future__ import division
import logging
from six import raise_from

from pacman.model.partitioner_interfaces.hand_over_to_vertex import \
    HandOverToVertex
from pacman.model.partitioner_interfaces.splitter_by_atoms import \
    SplitterByAtoms
from spinn_utilities.progress_bar import ProgressBar
from pacman.exceptions import PacmanPartitionException, PacmanValueError
from pacman.model.graphs.application.application_vertex import (
    ApplicationVertex)
from pacman.model.graphs.abstract_virtual_vertex import AbstractVirtualVertex
from pacman.model.constraints.partitioner_constraints import (
    AbstractPartitionerConstraint, MaxVertexAtomsConstraint,
    FixedVertexAtomsConstraint, SameAtomsAsVertexConstraint)
from pacman.model.graphs.common import GraphMapper, Slice
from pacman.model.graphs.machine import MachineGraph
from pacman.utilities import utility_calls as utils
from pacman.utilities.algorithm_utilities.partition_algorithm_utilities \
    import (
        generate_machine_edges, get_same_size_vertex_groups,
        get_remaining_constraints)
from pacman.utilities.algorithm_utilities.placer_algorithm_utilities import (
    sort_vertices_by_known_constraints)
from pacman.utilities.utility_objs import ResourceTracker

logger = logging.getLogger(__name__)


class PartitionAndPlacePartitioner(object):
    """ A partitioner that tries to ensure that SDRAM is not overloaded by\
        keeping track of the SDRAM usage on the various chips
    """

    __slots__ = []

    # inherited from AbstractPartitionAlgorithm
    def __call__(
            self, graph, machine, plan_n_timesteps,
            preallocated_resources=None):
        """
        :param graph: The application_graph to partition
        :type graph:\
            :py:class:`pacman.model.graph.application.ApplicationGraph`
        :param machine: The machine with respect to which to partition the\
            application_graph
        :type machine: :py:class:`spinn_machine.Machine`
        :param plan_n_timesteps: number of timesteps to plan for
        :type  plan_n_timesteps: int
        :return: \
            A machine_graph of partitioned vertices and partitioned edges
        :rtype:\
            :py:class:`pacman.model.graph.machine.MachineGraph`
        :raise pacman.exceptions.PacmanPartitionException: \
            If something goes wrong with the partitioning
        """
        ResourceTracker.check_constraints(graph.vertices)
        utils.check_algorithm_can_support_constraints(
            constrained_vertices=graph.vertices,
            abstract_constraint_type=AbstractPartitionerConstraint,
            supported_constraints=[MaxVertexAtomsConstraint,
                                   SameAtomsAsVertexConstraint,
                                   FixedVertexAtomsConstraint])

        # Load the vertices and create the machine_graph to fill
        machine_graph = MachineGraph(
            label="partitioned graph for {}".format(graph.label))
        graph_mapper = GraphMapper()

        # sort out vertex's by placement constraints
        vertices = sort_vertices_by_known_constraints(graph.vertices)

        # Set up the progress
        n_atoms = 0
        for vertex in vertices:
            n_atoms += vertex.n_atoms
        progress = ProgressBar(n_atoms, "Partitioning graph vertices")

        resource_tracker = ResourceTracker(
            machine, plan_n_timesteps,
            preallocated_resources=preallocated_resources)

        # Group vertices that are supposed to be the same size
        vertex_groups = get_same_size_vertex_groups(vertices)

        # Partition one vertex at a time
        for vertex in vertices:

            # check that the vertex hasn't already been partitioned
            machine_vertices = graph_mapper.get_machine_vertices(vertex)

            # if not, partition
            if machine_vertices is None:
                if isinstance(vertex, SplitterByAtoms):
                    self._partition_vertex(
                        vertex, plan_n_timesteps, machine_graph, graph_mapper,
                        resource_tracker, progress, vertex_groups)
                elif isinstance(vertex, HandOverToVertex):
                    vertex.create_and_add_to_graphs_and_resources(
                        resource_tracker, machine_graph, graph_mapper)
                    progress.update(vertex.n_atoms)
        progress.end()

        generate_machine_edges(machine_graph, graph_mapper, graph)

        return machine_graph, graph_mapper, resource_tracker.chips_used

    def _partition_vertex(
            self, vertex, plan_n_timesteps, machine_graph, graph_mapper,
            resource_tracker, progress, vertex_groups):
        """ Partition a single vertex

        :param vertex: the vertex to partition
        :type vertex:\
            :py:class:`pacman.model.graphs.application.ApplicationVertex`
        :param plan_n_timesteps: number of timesteps to plan for
        :type  plan_n_timesteps: int
        :param machine_graph: the graph to add vertices to
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param graph_mapper: the mappings between graphs
        :type graph_mapper:\
            :py:class:`pacman.model.graphs.common.GraphMapper'
        :param resource_tracker: A tracker of assigned resources
        :type resource_tracker:\
            :py:class:`pacman.utilities.ResourceTracker`
        :param progress: The progress bar
        :param vertex_groups: Groups together vertices that are supposed to\
            be the same size
        :rtype: None
        :raise pacman.exceptions.PacmanPartitionException: \
            if the extra vertex for partitioning identically has a different\
            number of atoms than its counterpart.
        """
        partition_together_vertices = list(vertex_groups[vertex])

        # locate max atoms per core and fixed atoms per core
        possible_max_atoms = list()
        n_atoms = None
        for other_vertex in partition_together_vertices:
            if isinstance(other_vertex, ApplicationVertex):
                possible_max_atoms.append(
                    other_vertex.get_max_atoms_per_core())
            max_atom_constraints = utils.locate_constraints_of_type(
                other_vertex.constraints, MaxVertexAtomsConstraint)
            for constraint in max_atom_constraints:
                possible_max_atoms.append(constraint.size)
            n_atom_constraints = utils.locate_constraints_of_type(
                other_vertex.constraints, FixedVertexAtomsConstraint)
            for constraint in n_atom_constraints:
                if n_atoms is not None and constraint.size != n_atoms:
                    raise PacmanPartitionException(
                        "Vertex has multiple contradictory fixed atom "
                        "constraints - cannot be both {} and {}".format(
                            n_atoms, constraint.size))
                n_atoms = constraint.size

        max_atoms_per_core = int(min(possible_max_atoms))
        if n_atoms is not None and max_atoms_per_core < n_atoms:
            raise PacmanPartitionException(
                "Max size of {} is incompatible with fixed size of {}".format(
                    max_atoms_per_core, n_atoms))
        if n_atoms is not None:
            max_atoms_per_core = n_atoms
            if vertex.n_atoms % n_atoms != 0:
                raise PacmanPartitionException(
                    "Vertex of {} atoms cannot be divided into units of {}"
                    .format(vertex.n_atoms, n_atoms))

        # partition by atoms
        self._partition_by_atoms(
            partition_together_vertices, plan_n_timesteps, vertex.n_atoms,
            max_atoms_per_core, machine_graph, graph_mapper, resource_tracker,
            progress, n_atoms is not None)

    def _partition_by_atoms(
            self, vertices, plan_n_timesteps, n_atoms, max_atoms_per_core,
            machine_graph, graph_mapper, resource_tracker, progress,
            fixed_n_atoms=False):
        """ Try to partition vertices on how many atoms it can fit on\
            each vertex

        :param vertices:\
            the vertexes that need to be partitioned at the same time
        :type vertices:\
            iterable list of\
            :py:class:`pacman.model.graphs.application.ApplicationVertex`
        :param plan_n_timesteps: number of timesteps to plan for
        :type  plan_n_timesteps: int
            iterable(:py:class:`pacman.model.graphs.application.ApplicationVertex`)
        :param n_atoms: the atoms of the first vertex
        :type n_atoms: int
        :param max_atoms_per_core:\
            the max atoms from all the vertexes considered that have max_atom\
            constraints
        :type max_atoms_per_core: int
        :param machine_graph: the machine graph
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param graph_mapper: the mapper between graphs
        :type graph_mapper:\
            :py:class:`pacman.model.graphs.common.GraphMapper'
        :param resource_tracker: A tracker of assigned resources
        :type resource_tracker:\
            :py:class:`pacman.utilities.ResourceTracker`
        :param progress: The progress bar
        :param fixed_n_atoms:\
            True if max_atoms_per_core is actually the fixed number of atoms\
            per core and cannot be reduced
        :type fixed_n_atoms: bool
        """
        n_atoms_placed = 0
        while n_atoms_placed < n_atoms:
            lo_atom = n_atoms_placed
            hi_atom = lo_atom + max_atoms_per_core - 1
            if hi_atom >= n_atoms:
                hi_atom = n_atoms - 1

            # Scale down the number of atoms to fit the available resources
            used_placements, hi_atom = self._scale_down_resources(
                lo_atom, hi_atom, vertices, plan_n_timesteps, resource_tracker,
                max_atoms_per_core, fixed_n_atoms)

            # Update where we are
            n_atoms_placed = hi_atom + 1

            # Create the vertices
            for (vertex, used_resources) in used_placements:
                vertex_slice = Slice(lo_atom, hi_atom)
                machine_vertex = vertex.create_machine_vertex(
                    vertex_slice, used_resources,
                    label="{}:{}:{}".format(vertex.label, lo_atom, hi_atom),
                    constraints=get_remaining_constraints(vertex))

                # update objects
                machine_graph.add_vertex(machine_vertex)
                graph_mapper.add_vertex_mapping(
                    machine_vertex, vertex_slice, vertex)

                progress.update(vertex_slice.n_atoms)

    @staticmethod
    def _reallocate_resources(
            used_placements, resource_tracker, lo_atom, hi_atom):
        """ Readjusts resource allocation and updates the placement list to\
            take into account the new layout of the atoms

        :param used_placements: \
            the original list of tuples containing placement data
        :type used_placements: iterable(tuple(7 items))
        :param resource_tracker: the tracker of resources
        :type resource_tracker:\
            :py:class:`pacman.utilities.ResourceTracker`
        :param lo_atom: the low atom of a slice to be considered
        :type lo_atom: int
        :param hi_atom: the high atom of a slice to be considered
        :type hi_atom: int
        :return: the new list of tuples containing placement data
        :rtype: iterable(tuple(7 items))
        """

        new_used_placements = list()
        for (placed_vertex, x, y, p, placed_resources,
                ip_tags, reverse_ip_tags) in used_placements:

            if not isinstance(placed_vertex, AbstractVirtualVertex):
                # Deallocate the existing resources
                resource_tracker.unallocate_resources(
                    x, y, p, placed_resources, ip_tags, reverse_ip_tags)

            # Get the new resource usage
            vertex_slice = Slice(lo_atom, hi_atom)
            new_resources = \
                placed_vertex.get_resources_used_by_atoms(vertex_slice)

            if not isinstance(placed_vertex, AbstractVirtualVertex):
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
            self, lo_atom, hi_atom, vertices, plan_n_timesteps,
            resource_tracker, max_atoms_per_core, fixed_n_atoms=False):
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
            :py:class:`pacman.model.graphs.application.ApplicationVertex`
        :param plan_n_timesteps: number of timesteps to plan for
        :type  plan_n_timesteps: int
            iterable(:py:class:`pacman.model.graphs.application.ApplicationVertex`)
        :param max_atoms_per_core:\
            the max atoms from all the vertexes considered that have max_atom\
            constraints
        :type max_atoms_per_core: int
        :param resource_tracker: Tracker of used resources
        :type resource_tracker: :py:class:`spinn_machine.Machine`
        :param fixed_n_atoms:\
            True if max_atoms_per_core is actually the fixed number of atoms\
            per core
        :type fixed_n_atoms: bool
        :return: the list of placements made by this method and the new amount\
            of atoms partitioned
        :rtype: tuple(iterable(tuple(2 items)), int)
        :raise PacmanPartitionException: when the vertex cannot be partitioned
        """
        used_placements = list()

        # Find the number of atoms that will fit in each vertex given the
        # resources available
        min_hi_atom = hi_atom
        for vertex in vertices:

            # get resources used by vertex
            vertex_slice = Slice(lo_atom, hi_atom)
            used_resources = vertex.get_resources_used_by_atoms(vertex_slice)

            x = None
            y = None
            p = None
            ip_tags = None
            reverse_ip_tags = None
            if not isinstance(vertex, AbstractVirtualVertex):

                # get max resources_available on machine
                resources_available = resource_tracker\
                    .get_maximum_constrained_resources_available(
                        used_resources, vertex.constraints)

                # Work out the ratio of used to available resources
                ratio = self._find_max_ratio(
                    used_resources, resources_available, plan_n_timesteps)

                if fixed_n_atoms and ratio > 1.0:
                    raise PacmanPartitionException(
                        "No more of vertex '{}' would fit on the board:\n"
                        "    Allocated so far: {} atoms\n"
                        "    Request for SDRAM: {}\n"
                        "    Largest SDRAM space: {}".format(
                            vertex, lo_atom - 1,
                            used_resources.sdram.get_total_sdram(
                                plan_n_timesteps),
                            resources_available.sdram.get_total_sdram(
                                plan_n_timesteps)))

                while ratio > 1.0 and hi_atom >= lo_atom:
                    # Scale the resources available by the ratio
                    old_n_atoms = (hi_atom - lo_atom) + 1
                    new_n_atoms = int(old_n_atoms / (ratio * 1.1))

                    # Avoid infinite looping
                    if old_n_atoms == new_n_atoms:
                        new_n_atoms -= 1

                    # Find the new resource usage
                    hi_atom = lo_atom + new_n_atoms - 1
                    if hi_atom >= lo_atom:
                        vertex_slice = Slice(lo_atom, hi_atom)
                        used_resources = \
                            vertex.get_resources_used_by_atoms(vertex_slice)
                        ratio = self._find_max_ratio(
                            used_resources, resources_available,
                            plan_n_timesteps)

                # If we couldn't partition, raise an exception
                if hi_atom < lo_atom:
                    raise PacmanPartitionException(
                        "No more of vertex '{}' would fit on the board:\n"
                        "    Allocated so far: {} atoms\n"
                        "    Request for SDRAM: {}\n"
                        "    Largest SDRAM space: {}".format(
                            vertex, lo_atom - 1,
                            used_resources.sdram.get_total_sdram(
                                plan_n_timesteps),
                            resources_available.sdram.get_total_sdram(
                                plan_n_timesteps)))

                # Try to scale up until just below the resource usage
                used_resources, hi_atom = self._scale_up_resource_usage(
                    used_resources, hi_atom, lo_atom, max_atoms_per_core,
                    vertex, plan_n_timesteps, resources_available, ratio)

                # If this hi_atom is smaller than the current minimum, update
                # the other placements to use (hopefully) less
                # resources available
                if hi_atom < min_hi_atom:
                    min_hi_atom = hi_atom
                    used_placements = self._reallocate_resources(
                        used_placements, resource_tracker, lo_atom, hi_atom)

                # Attempt to allocate the resources available for this vertex
                # on the machine
                try:
                    (x, y, p, ip_tags, reverse_ip_tags) = \
                        resource_tracker.allocate_constrained_resources(
                            used_resources, vertex.constraints)
                except PacmanValueError as e:
                    raise_from(PacmanValueError(
                        "Unable to allocate requested resources available to"
                        " vertex '{}':\n{}".format(vertex, e)), e)

            used_placements.append((vertex, x, y, p, used_resources,
                                    ip_tags, reverse_ip_tags))

        # reduce data to what the parent requires
        final_placements = list()
        for (vertex, _, _, _, used_resources, _, _) in used_placements:
            final_placements.append((vertex, used_resources))

        return final_placements, min_hi_atom

    def _scale_up_resource_usage(
            self, used_resources, hi_atom, lo_atom, max_atoms_per_core, vertex,
            plan_n_timesteps, resources, ratio):
        """ Try to push up the number of atoms in a vertex to be as close\
            to the available resources as possible

        :param used_resources: the resources used by the machine so far
        :type used_resources:\
            :py:class:`pacman.model.resources.Resource`
        :param hi_atom: the total number of atoms to place for this vertex
        :type hi_atom: int
        :param lo_atom: the number of atoms already partitioned
        :type lo_atom: int
        :param max_atoms_per_core: the min max atoms from all the vertexes \
            considered that have max_atom constraints
        :type max_atoms_per_core: int
        :param vertex: the vertexes to scale up the num atoms per core for
        :type vertex:\
            :py:class:`pacman.model.graphs.application.ApplicationVertex`
        :param plan_n_timesteps: number of timesteps to plan for
        :type  plan_n_timesteps: int
        :param resources: the resource estimate for the vertex for a given\
            number of atoms
        :type resources:\
            :py:class:`pacman.model.resources.Resource`
        :param ratio: the ratio between max atoms and available resources
        :type ratio: int
        :return: the new resources used and the new hi_atom
        :rtype: tuple(:py:class:`pacman.model.resources.Resource`, int)
        """

        previous_used_resources = used_resources
        previous_hi_atom = hi_atom

        # Keep searching while the ratio is still in range,
        # the next hi_atom value is still less than the number of atoms,
        # and the number of atoms is less than the constrained number of atoms
        while ((ratio < 1.0) and (hi_atom + 1 < vertex.n_atoms) and
               (hi_atom - lo_atom + 2 < max_atoms_per_core)):

            # Update the hi_atom, keeping track of the last hi_atom which
            # resulted in a ratio < 1.0
            previous_hi_atom = hi_atom
            hi_atom += 1

            # Find the new resource usage, keeping track of the last usage
            # which resulted in a ratio < 1.0
            previous_used_resources = used_resources
            vertex_slice = Slice(lo_atom, hi_atom)
            used_resources = vertex.get_resources_used_by_atoms(vertex_slice)
            ratio = self._find_max_ratio(
                used_resources, resources, plan_n_timesteps)

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
        :type vertices: \
            iterable(:py:class:`pacman.model.graphs.application.ApplicationVertex`)
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
    def _ratio(numerator, denominator):
        """Get the ratio between two values, with special\
        handling for when the denominator is zero.
        """
        if denominator == 0:
            return 0
        return numerator / denominator

    @staticmethod
    def _find_max_ratio(required, available, plan_n_timesteps):
        """ Find the max ratio between the resources

        :param required: the resources used by the vertex
        :type required:\
            :py:class:`pacman.model.resources.ResourceContainer`
        :param available: the max resources available from the machine
        :type available: \
            :py:class:`pacman.model.resources.ResourceContainer`
        :return: the largest ratio of resources
        :param plan_n_timesteps: number of timesteps to plan for
        :type  plan_n_timesteps: int
        :rtype: int
        :raise None: this method does not raise any known exceptions

        """
        cpu_ratio = PartitionAndPlacePartitioner._ratio(
            required.cpu_cycles.get_value(), available.cpu_cycles.get_value())
        dtcm_ratio = PartitionAndPlacePartitioner._ratio(
            required.dtcm.get_value(), available.dtcm.get_value())
        sdram_ratio = PartitionAndPlacePartitioner._ratio(
            required.sdram.get_total_sdram(plan_n_timesteps),
            available.sdram.get_total_sdram(plan_n_timesteps))
        return max((cpu_ratio, dtcm_ratio, sdram_ratio))
