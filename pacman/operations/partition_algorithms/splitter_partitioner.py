# Copyright (c) 2020-2021 The University of Manchester
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
from collections import OrderedDict

from pacman.exceptions import (
    PacmanConfigurationException, PacmanPartitionException)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint)
from pacman.model.graphs.machine import MachineGraph
from pacman.model.partitioner_interfaces import (
    AbstractSplitterPartitioner, AbstractSlicesConnect)
from pacman.model.partitioner_splitters.abstract_splitters\
    .abstract_dependent_splitter import AbstractDependentSplitter
from pacman.utilities.algorithm_utilities. \
    partition_algorithm_utilities import get_same_size_vertex_groups
from pacman.utilities.algorithm_utilities.placer_algorithm_utilities import (
    sort_vertices_by_known_constraints)
from pacman.utilities.utility_objs import ResourceTracker
from spinn_utilities.overrides import overrides
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities import utility_calls as utils


class SplitterPartitioner(AbstractSplitterPartitioner):
    """ partitioner which hands the partitioning work to app vertices
    splitter objects.

    :param ApplicationGraph app_graph: The application_graph to partition
    :param ~spinn_machine.Machine machine:
        The machine with respect to which to partition the application
        graph
    :param int or None plan_n_time_steps: number of time steps to plan for
    :param pre_allocated_resources:
    :type pre_allocated_resources: PreAllocatedResourceContainer or None
    :return:
        A machine_graph of partitioned vertices and partitioned edges,
        and the number of chips needed to satisfy this partitioning.
    :rtype: tuple(MachineGraph, int)
    :raise PacmanPartitionException:
        If something goes wrong with the partitioning
    """

    MACHINE_EDGE_LABEL = "machine_edge_for_{}"

    __PROGRESS_BAR_VERTICES = "Partitioning graph vertices"
    __PROGRESS_BAR_EDGES = "Partitioning graph edges"

    __ERROR_MESSAGE_OF_NO_COMMON_EDGE_TYPE = (
        "There was no common edge type between vertex {} and {}. "
        "This means there is no agreed way these 2 vertices can "
        "communicate with each and therefore a machine edge cannot "
        "be created. Please fix and try again")

    __ERROR_MESSAGE_CONFLICT_FIXED_ATOM = (
        "Vertex has multiple contradictory fixed atom "
        "constraints - cannot be both {} and {}")

    __ERROR_MESSAGE_CONFLICT_MAX_ATOMS = (
        "Max size of {} is incompatible with fixed size of {}")

    __ERROR_MESSAGE_FAILED_DIVISION = (
        "Vertex of {} atoms cannot be divided into units of {}")

    __slots__ = []

    # inherited from AbstractPartitionAlgorithm
    def __call__(
            self, app_graph, machine, plan_n_time_steps,
            pre_allocated_resources=None):
        """
        :param ApplicationGraph app_graph: app graph
        :param ~spinn_machine.Machine machine: machine rep
        :param int or None plan_n_time_steps: \
            the number of time steps to run for
        :param pre_allocated_resources: res needed to be pre allocated before\
            making new machine vertices.
        :type pre_allocated_resources: PreAllocatedResourceContainer or None
        :rtype: tuple(MachineGraph, int)
        :raise PacmanPartitionException:
        """

        # check resource tracker can handle constraints
        ResourceTracker.check_constraints(app_graph.vertices)

        # get the setup objects
        (machine_graph, resource_tracker, vertices, progress) = (
            self.__setup_objects(
                app_graph, machine, plan_n_time_steps,
                pre_allocated_resources))

        self.__set_same_max_atoms_to_splitters(app_graph)

        # Partition one vertex at a time
        for vertex in progress.over(vertices):
            vertex.splitter_object.split(resource_tracker, machine_graph)

        # process edges
        self.__process_machine_edges(
            app_graph, machine_graph, resource_tracker)

        # return the accepted things
        return machine_graph, resource_tracker.chips_used

    @staticmethod
    def order_vertices_for_dependent_splitters(vertices):
        """ orders the list so that dependent splitters are next to their other
        splitter in terms of vertex ordering.

        :param vertices: the list of application vertices
        :type vertices: iterable of ApplicationVertex
        :return: vertices in list with new ordering
        :rtype: iterable of ApplicationVertex
        """
        dependent_vertices = OrderedDict()
        for vertex in vertices:
            if isinstance(vertex.splitter_object, AbstractDependentSplitter):
                other_app_vertex = (
                    vertex.splitter_object.other_splitter.governed_app_vertex)
                dependent_vertices[other_app_vertex] = vertex

        for main_vertex in dependent_vertices.keys():
            old_index_of_dependent = (
                vertices.index(dependent_vertices[main_vertex]))
            next_to_index = vertices.index(main_vertex) + 1
            vertices.insert(next_to_index,
                            vertices.pop(old_index_of_dependent))
        return vertices

    def __set_same_max_atoms_to_splitters(self, app_graph):
        """ get the constraints sorted out.

        :param ApplicationGraph app_graph: the app graph
        :rtype: None
        """
        # Group vertices that are supposed to be the same size
        vertex_groups = get_same_size_vertex_groups(app_graph.vertices)
        for vertex in app_graph.vertices:
            partition_together_vertices = list(vertex_groups[vertex])

            # locate max atoms per core and fixed atoms per core
            possible_max_atoms = list()
            fixed_n_atoms = None
            for other_vertex in partition_together_vertices:
                possible_max_atoms.append(
                    other_vertex.get_max_atoms_per_core())
                max_atom_constraints = utils.locate_constraints_of_type(
                    other_vertex.constraints, MaxVertexAtomsConstraint)
                for constraint in max_atom_constraints:
                    possible_max_atoms.append(constraint.size)
                n_atom_constraints = utils.locate_constraints_of_type(
                    other_vertex.constraints, FixedVertexAtomsConstraint)
                for constraint in n_atom_constraints:
                    if (fixed_n_atoms is not None and
                            constraint.size != fixed_n_atoms):
                        raise PacmanPartitionException(
                            self.__ERROR_MESSAGE_CONFLICT_FIXED_ATOM.format(
                                fixed_n_atoms, constraint.size))
                    fixed_n_atoms = constraint.size

            max_atoms_per_core = int(min(possible_max_atoms))
            if (fixed_n_atoms is not None and
                    max_atoms_per_core < fixed_n_atoms):
                raise PacmanPartitionException(
                    self.__ERROR_MESSAGE_CONFLICT_MAX_ATOMS.format(
                        max_atoms_per_core, fixed_n_atoms))
            if fixed_n_atoms is not None:
                max_atoms_per_core = fixed_n_atoms
                if vertex.n_atoms % fixed_n_atoms != 0:
                    raise PacmanPartitionException(
                        self.__ERROR_MESSAGE_FAILED_DIVISION.format(
                            vertex.n_atoms, fixed_n_atoms))

            for other_vertex in partition_together_vertices:
                other_vertex.splitter_object.set_max_atoms_per_core(
                    max_atoms_per_core, fixed_n_atoms is not None)
            vertex.splitter_object.set_max_atoms_per_core(
                max_atoms_per_core, fixed_n_atoms is not None)

    def __setup_objects(
            self, app_graph, machine, plan_n_time_steps,
            pre_allocated_resources):
        """ sets up the machine_graph, resource_tracker, vertices, \
        progress bar.

        :param ApplicationGraph app_graph: app graph
        :param ~spinn_machine.Machine machine: machine
        :param int plan_n_time_steps: the number of time steps to run for.
        :param pre_allocated_resources: pre allocated res from other systems.
        :type PreAllocatedResourceContainer or None
        :return:
        """
        # Load the vertices and create the machine_graph to fill
        machine_graph = MachineGraph(
            label="partitioned graph for {}".format(app_graph.label),
            application_graph=app_graph)

        resource_tracker = ResourceTracker(
            machine, plan_n_time_steps,
            preallocated_resources=pre_allocated_resources)

        # sort out vertex's by placement constraints
        vertices = sort_vertices_by_known_constraints(app_graph.vertices)

        # Group vertices that are supposed to be the same size
        vertices = self.order_vertices_for_dependent_splitters(vertices)

        # Set up the progress
        progress = ProgressBar(
            len(app_graph.vertices), self.__PROGRESS_BAR_VERTICES)

        return machine_graph, resource_tracker, vertices, progress

    def __locate_common_edge_type(
            self, pre_edge_types, post_edge_types, src_machine_vertex,
            dest_machine_vertex):
        """ searches the sets of edge types and finds the common one. if more
        than one common, is biased towards the destination common and the
        order of the list.

        :param pre_edge_types: the edge types the pre vertex can support for \
        transmission
        :param post_edge_types: the edge types the post vertex can support \
        for reception.
        :param MachineVertex src_machine_vertex: used for error message
        :param MachineVertex dest_machine_vertex: used for error message
        :return: MachineEdge class
        """
        for post_edge_type in post_edge_types:
            if post_edge_type in pre_edge_types:
                return post_edge_type

        # if iterated over the post edge types and not found a common type.
        # Blow up coz no way these two can communicate with each other.
        raise PacmanConfigurationException(
            self.__ERROR_MESSAGE_OF_NO_COMMON_EDGE_TYPE.format(
                src_machine_vertex, dest_machine_vertex))

    def __process_machine_edges(
            self, app_graph, machine_graph, resource_tracker):
        """ generate the machine edges for the machine graph

        :param ApplicationGraph app_graph: app graph
        :param MachineGraph machine_graph: machine graph
        :param ResourceTracker resource_tracker: resource tracker
        :rtype: None
        """

        # process edges
        progress = ProgressBar(
            app_graph.n_outgoing_edge_partitions, self.__PROGRESS_BAR_EDGES)

        # go over outgoing partitions
        for app_outgoing_edge_partition in progress.over(
                app_graph.outgoing_edge_partitions):

            # go through each edge
            for app_edge in app_outgoing_edge_partition.edges:
                src_vertices_edge_type_map = (
                    app_edge.pre_vertex.splitter_object.get_out_going_vertices(
                        app_edge, app_outgoing_edge_partition))

                # go through each pre vertices
                for src_machine_vertex in src_vertices_edge_type_map:
                    splitter = app_edge.post_vertex.splitter_object
                    dest_vertices_edge_type_map = (
                        splitter.get_in_coming_vertices(
                            app_edge, app_outgoing_edge_partition,
                            src_machine_vertex))

                    # go through the post vertices
                    for dest_machine_vertex in dest_vertices_edge_type_map:
                        # get the accepted edge types for each vertex
                        pre_edge_types = (
                            src_vertices_edge_type_map[src_machine_vertex])
                        post_edge_types = (
                            dest_vertices_edge_type_map[dest_machine_vertex])

                        # locate the common edge type
                        common_edge_type = self.__locate_common_edge_type(
                            pre_edge_types, post_edge_types,
                            src_machine_vertex, dest_machine_vertex)

                        self.create_machine_edge(
                            src_machine_vertex, dest_machine_vertex,
                            common_edge_type, app_edge, machine_graph,
                            app_outgoing_edge_partition, resource_tracker)

    @overrides(AbstractSplitterPartitioner.create_machine_edge)
    def create_machine_edge(
            self, src_machine_vertex, dest_machine_vertex,
            common_edge_type, app_edge, machine_graph,
            app_outgoing_edge_partition, resource_tracker):
        """ overridable method for creating the machine edges

        :param MachineVertex src_machine_vertex: \
            src machine vertex of the edge.
        :param MachineVertex dest_machine_vertex: \
            dest machine vertex of the edge.
        :param MachineEdge common_edge_type: the edge type to build.
        :param ApplicationEdge app_edge: the app edge to associate the\
            machine edge with.
        :param MachineGraph machine_graph: machine graph
        :param Resource resource_tracker: res tracker.
        :param OutgoingEdgePartition app_outgoing_edge_partition: partition.
        :rtype: None
        """

        if (isinstance(app_edge, AbstractSlicesConnect) and not
                app_edge.could_connect(
                    src_machine_vertex.vertex_slice,
                    dest_machine_vertex.vertex_slice)):
            return

        # build edge and add to machine graph
        machine_edge = common_edge_type(
            src_machine_vertex, dest_machine_vertex, app_edge=app_edge,
            label=self.MACHINE_EDGE_LABEL.format(app_edge.label))
        machine_graph.add_edge(
            machine_edge, app_outgoing_edge_partition.identifier)
