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
from pacman.exceptions import (PacmanConfigurationException)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint)
from pacman.model.graphs.machine import MachineGraph
from pacman.model.partitioner_interfaces import (
    AbstractSplitterPartitioner, AbstractSlicesConnect)
from pacman.model.partitioner_splitters.abstract_splitters\
    .abstract_dependent_splitter import AbstractDependentSplitter
from pacman.utilities.algorithm_utilities.placer_algorithm_utilities import (
    sort_vertices_by_known_constraints)
from pacman.utilities.utility_objs import ResourceTracker
from spinn_utilities.overrides import overrides
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities import utility_calls as utils


def splitter_partitioner(
        app_graph, machine, plan_n_time_steps, pre_allocated_resources=None):
    """
     :param ApplicationGraph app_graph: The application_graph to partition
     :param ~spinn_machine.Machine machine:
         The machine with respect to which to partition the application
         graph
     :param plan_n_time_steps:
         the number of time steps to plan to run for
     :type plan_n_time_steps: int or None
     :param pre_allocated_resources:
         res needed to be preallocated before making new machine vertices
     :type pre_allocated_resources: PreAllocatedResourceContainer or None
     :return:
         A machine_graph of partitioned vertices and partitioned edges,
         and the number of chips needed to satisfy this partitioning.
     :rtype: tuple(MachineGraph, int)
     :raise PacmanPartitionException:
         If something goes wrong with the partitioning
     """
    partitioner = _SplitterPartitioner()
    partitioner._run(
        app_graph, machine, plan_n_time_steps, pre_allocated_resources)


class _SplitterPartitioner(AbstractSplitterPartitioner):
    """ Partitioner which hands the partitioning work to application vertices'\
        splitter objects.
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
    def _run(
            self, app_graph, machine, plan_n_time_steps,
            pre_allocated_resources=None):
        """
        :param ApplicationGraph app_graph: The application_graph to partition
        :param ~spinn_machine.Machine machine:
            The machine with respect to which to partition the application
            graph
        :param plan_n_time_steps:
            the number of time steps to plan to run for
        :type plan_n_time_steps: int or None
        :param pre_allocated_resources:
            res needed to be preallocated before making new machine vertices
        :type pre_allocated_resources: PreAllocatedResourceContainer or None
        :return:
            A machine_graph of partitioned vertices and partitioned edges,
            and the number of chips needed to satisfy this partitioning.
        :rtype: tuple(MachineGraph, int)
        :raise PacmanPartitionException:
            If something goes wrong with the partitioning
        """

        # check resource tracker can handle constraints
        ResourceTracker.check_constraints(app_graph.vertices)

        # get the setup objects
        (machine_graph, resource_tracker, vertices, progress) = (
            self.__setup_objects(
                app_graph, machine, plan_n_time_steps,
                pre_allocated_resources))

        self.__set_max_atoms_to_splitters(app_graph)

        # Partition one vertex at a time
        for vertex in progress.over(vertices):
            vertex.splitter.split(resource_tracker, machine_graph)

        # process edges
        self.__process_machine_edges(
            app_graph, machine_graph, resource_tracker)

        # return the accepted things
        return machine_graph, resource_tracker.chips_used

    def __make_dependent_after(self, vertices, dependent_vertices, dependent):
        """ orders the vertices so that dependents are split after the\
            things they depend upon.

        :param list(MachineVertex) vertices: machine vertices
        :param list(ApplicationVertex) dependent_vertices:
            list of dependent vertices
        :param ApplicationVertex dependent:
            the vertex that's dependent on things.
        """
        if dependent in dependent_vertices:
            other_app_vertex = dependent_vertices[dependent]
            # check the other is not also dependent
            self.__make_dependent_after(
                vertices, dependent_vertices, other_app_vertex)
            old_index = vertices.index(dependent)
            other_index = vertices.index(other_app_vertex)
            if old_index < other_index:
                vertices.insert(other_index + 1, vertices.pop(old_index))

    def order_vertices_for_dependent_splitters(self, vertices):
        """ orders the list so that dependent splitters are next to their \
            other splitter in terms of vertex ordering.

        :param iterable(ApplicationVertex) vertices:
            the list of application vertices
        :return: vertices in list with new ordering
        :rtype: iterable(ApplicationVertex)
        """
        dependent_vertices = OrderedDict()
        other_vertices = set()
        for vertex in vertices:
            if isinstance(vertex.splitter, AbstractDependentSplitter):
                other_splitter = vertex.splitter.other_splitter
                if other_splitter:
                    other_app_vertex = other_splitter.governed_app_vertex
                    other_vertices.add(other_app_vertex)
                    dependent_vertices[vertex] = other_app_vertex

        for vertex in dependent_vertices:
            # As we do the whole dependency chain only start at the bottom
            if vertex not in other_vertices:
                self.__make_dependent_after(
                    vertices, dependent_vertices, vertex)

    @staticmethod
    def __set_max_atoms_to_splitters(app_graph):
        """ get the constraints sorted out.

        :param ApplicationGraph app_graph: the app graph
        """
        for vertex in app_graph.vertices:
            for constraint in utils.locate_constraints_of_type(
                    vertex.constraints, MaxVertexAtomsConstraint):
                vertex.splitter.set_max_atoms_per_core(
                    constraint.size, False)
            for constraint in utils.locate_constraints_of_type(
                    vertex.constraints, FixedVertexAtomsConstraint):
                vertex.splitter.set_max_atoms_per_core(
                    constraint.size, True)

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
        :return: (machine graph, res tracker, verts, progress bar)
        :rtype: tuple(MachineGraph, ResourceTracker, list(ApplicationVertex),
            ~.ProgressBar)
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
        self.order_vertices_for_dependent_splitters(vertices)

        # Set up the progress
        progress = ProgressBar(
            len(app_graph.vertices), self.__PROGRESS_BAR_VERTICES)

        return machine_graph, resource_tracker, vertices, progress

    def __locate_common_edge_type(
            self, pre_edge_types, post_edge_types, src_machine_vertex,
            dest_machine_vertex):
        """ searches the sets of edge types and finds the common one. if more\
            than one common, is biased towards the destination common and the\
            order of the list.

        :param pre_edge_types:
            the edge types the pre vertex can support for transmission
        :param post_edge_types:
            the edge types the post vertex can support for reception.
        :param MachineVertex src_machine_vertex: used for error message
        :param MachineVertex dest_machine_vertex: used for error message
        :return: MachineEdge class
        :rtype: type
        :raises PacmanConfigurationException:
            If we can't find a workable class
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
                    app_edge.pre_vertex.splitter.get_out_going_vertices(
                        app_edge, app_outgoing_edge_partition))

                # go through each pre vertices
                for src_machine_vertex in src_vertices_edge_type_map:
                    splitter = app_edge.post_vertex.splitter
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

        if (isinstance(app_edge, AbstractSlicesConnect) and not
                app_edge.could_connect(
                    src_machine_vertex,  dest_machine_vertex)):
            return

        # build edge and add to machine graph
        machine_edge = common_edge_type(
            src_machine_vertex, dest_machine_vertex, app_edge=app_edge,
            label=self.MACHINE_EDGE_LABEL.format(app_edge.label))
        machine_graph.add_edge(
            machine_edge, app_outgoing_edge_partition.identifier)
