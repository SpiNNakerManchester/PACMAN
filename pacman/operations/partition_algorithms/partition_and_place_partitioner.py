# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
import logging
from six import raise_from

from pacman.model.partitioner_interfaces.hand_over_to_vertex import \
    HandOverToVertex
from pacman.model.partitioner_interfaces.splitter_by_atoms import \
    SplitterByAtoms
from spinn_utilities.progress_bar import ProgressBar
from pacman.exceptions import PacmanPartitionException, PacmanValueError
from pacman.model.graphs.abstract_virtual import AbstractVirtual
from pacman.model.constraints.partitioner_constraints import (
    AbstractPartitionerConstraint, MaxVertexAtomsConstraint,
    FixedVertexAtomsConstraint, SameAtomsAsVertexConstraint)
from pacman.model.graphs.common import Slice
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

    :param ApplicationGraph graph: The application_graph to partition
    :param ~spinn_machine.Machine machine:
        The machine with respect to which to partition the application
        graph
    :param int plan_n_timesteps: number of timesteps to plan for
    :param preallocated_resources:
    :type preallocated_resources: PreAllocatedResourceContainer or None
    :return:
        A machine_graph of partitioned vertices and partitioned edges,
        and the number of chips needed to satisfy this partitioning.
    :rtype: tuple(MachineGraph, int)
    :raise PacmanPartitionException:
        If something goes wrong with the partitioning
    """

    __slots__ = []

    # inherited from AbstractPartitionAlgorithm
    def __call__(
            self, graph, machine, plan_n_timesteps,
            preallocated_resources=None):
        """
        :param ApplicationGraph graph:
        :param ~spinn_machine.Machine machine:
        :param int plan_n_timesteps:
        :param preallocated_resources:
        :type preallocated_resources: PreAllocatedResourceContainer or None
        :rtype: tuple(MachineGraph, int)
        :raise PacmanPartitionException:
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
            label="partitioned graph for {}".format(graph.label),
            application_graph=graph)

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
            # if no existing machine vertices, partition
            if not vertex.machine_vertices:
                if isinstance(vertex, SplitterByAtoms):
                    self._partition_vertex(
                        vertex, plan_n_timesteps, machine_graph,
                        resource_tracker, progress, vertex_groups)
                elif isinstance(vertex, HandOverToVertex):
                    vertex.create_and_add_to_graphs_and_resources(
                        resource_tracker, machine_graph, graph_mapper)
                    progress.update(vertex.n_atoms)
                else:
                    raise Exception(
                        "The vertex type {} is neither a SpillerByAtoms nor "
                        "a HandOverToVertex vertex type. This partitioner "
                        "does not know how to handle vertices which are not "
                        "1 of these types. Please fix and try again")
        progress.end()

        generate_machine_edges(machine_graph, graph)

        return machine_graph, resource_tracker.chips_used

    def _partition_vertex(
            self, vertex, plan_n_timesteps, machine_graph,
            resource_tracker, progress, vertex_groups):
        """ Partition a single vertex

        :param ApplicationVertex vertex: the vertex to partition
        :param int plan_n_timesteps: number of timesteps to plan for
        :param MachineGraph machine_graph: the graph to add vertices to
        :param ResourceTracker resource_tracker:
            A tracker of assigned resources
        :param ~spinn_utilities.progress_bar.ProgressBar progress:
            The progress bar
        :param vertex_groups:
            Groups together vertices that are supposed to be the same size
        :type vertex_groups: dict(ApplicationVertex, list(ApplicationVertex))
        :rtype: None
        :raise PacmanPartitionException:
            if the extra vertex for partitioning identically has a different
            number of atoms than its counterpart.
        """
        partition_together_vertices = list(vertex_groups[vertex])

        # locate max atoms per core and fixed atoms per core
        possible_max_atoms = list()
        n_atoms = None
        for other_vertex in partition_together_vertices:
            possible_max_atoms.append(other_vertex.get_max_atoms_per_core())
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
            max_atoms_per_core, machine_graph, resource_tracker,
            progress, n_atoms is not None)

    def _partition_by_atoms(
            self, vertices, plan_n_timesteps, n_atoms, max_atoms_per_core,
            machine_graph, resource_tracker, progress, fixed_n_atoms=False):
        """ Try to partition vertices on how many atoms it can fit on\
            each vertex

        :param iterable(ApplicationVertex) vertices:
            the vertexes that need to be partitioned at the same time
        :param int plan_n_timesteps: number of timesteps to plan for
        :param int n_atoms: the atoms of the first vertex
        :param int max_atoms_per_core:
            the max atoms from all the vertexes considered that have max_atom
            constraints
        :param MachineGraph machine_graph: the machine graph
        :param ResourceTracker resource_tracker:
            A tracker of assigned resources
        :param ~spinn_utilities.progress_bar.ProgressBar progress:
            The progress bar
        :param bool fixed_n_atoms:
            True if `max_atoms_per_core` is actually the fixed number of atoms
            per core and cannot be reduced
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
                progress.update(vertex_slice.n_atoms)

    @staticmethod
    def _reallocate_resources(
            used_placements, resource_tracker, lo_atom, hi_atom):
        """ Readjusts resource allocation and updates the placement list to\
            take into account the new layout of the atoms

        :param used_placements:
            the original list of tuples containing placement data
        :type used_placements: list(tuple(
            ApplicationVertex, int, int, int, ResourceContainer,
            list(tuple(int, int)), list(tuple(int, int))))
        :param ResourceTracker resource_tracker: the tracker of resources
        :param int lo_atom: the low atom of a slice to be considered
        :param int hi_atom: the high atom of a slice to be considered
        :return: the new list of tuples containing placement data
        :rtype: list(tuple(
            ApplicationVertex, int, int, int, ResourceContainer,
            list(tuple(int, int)), list(tuple(int, int))))
        """

        new_used_placements = list()
        for (placed_vertex, x, y, p, placed_resources,
                ip_tags, reverse_ip_tags) in used_placements:

            if not isinstance(placed_vertex, AbstractVirtual):
                # Deallocate the existing resources
                resource_tracker.unallocate_resources(
                    x, y, p, placed_resources, ip_tags, reverse_ip_tags)

            # Get the new resource usage
            vertex_slice = Slice(lo_atom, hi_atom)
            new_resources = placed_vertex.get_resources_used_by_atoms(
                vertex_slice)

            if not isinstance(placed_vertex, AbstractVirtual):
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

        :param int lo_atom: the number of atoms already partitioned
        :param int hi_atom: the total number of atoms to place for this vertex
        :param iterable(ApplicationVertex) vertices:
            the vertexes that need to be partitioned at the same time
        :param int plan_n_timesteps: number of timesteps to plan for
        :param int max_atoms_per_core:
            the max atoms from all the vertexes considered that have max_atom
            constraints
        :param ResourceTracker resource_tracker: Tracker of used resources
        :param bool fixed_n_atoms:
            True if max_atoms_per_core is actually the fixed number of atoms
            per core
        :return: the list of placements made by this method and the new amount
            of atoms partitioned
        :rtype: tuple(iterable(tuple(ApplicationVertex, ResourceContainer)),
            int)
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
            if not isinstance(vertex, AbstractVirtual):

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

        :param ResourceContainer used_resources:
            the resources used by the machine so far
        :param int hi_atom: the total number of atoms to place for this vertex
        :param int lo_atom: the number of atoms already partitioned
        :param int max_atoms_per_core: the min max atoms from all the vertexes
            considered that have max_atom constraints
        :param ApplicationVertex vertex:
            the vertex to scale up the num atoms per core for
        :param int plan_n_timesteps: number of timesteps to plan for
        :param ResourceContainer resources:
            the resource estimate for the vertex for a given number of atoms
        :param float ratio: the ratio between max atoms and available resources
        :return: the new resources used and the new hi_atom
        :rtype: tuple(ResourceContainer, int)
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

        :param iterable(ApplicationVertex) vertices:
            a iterable list of vertices
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
        """ Get the ratio between two values, with special handling for when\
            the denominator is zero.

        :param int numerator:
        :param int denominator:
        :rtype: float
        """
        if denominator == 0:
            return 0.0
        return numerator / denominator

    @classmethod
    def _find_max_ratio(cls, required, available, plan_n_timesteps):
        """ Find the max ratio between the resources.

        :param ResourceContainer required: the resources used by the vertex
        :param ResourceContainer available:
            the max resources available from the machine
        :param int plan_n_timesteps: number of timesteps to plan for
        :return: the largest ratio of resources
        :rtype: float
        :raise None: this method does not raise any known exceptions
        """
        cpu_ratio = cls._ratio(
            required.cpu_cycles.get_value(), available.cpu_cycles.get_value())
        dtcm_ratio = cls._ratio(
            required.dtcm.get_value(), available.dtcm.get_value())
        sdram_ratio = cls._ratio(
            required.sdram.get_total_sdram(plan_n_timesteps),
            available.sdram.get_total_sdram(plan_n_timesteps))
        return max((cpu_ratio, dtcm_ratio, sdram_ratio))
