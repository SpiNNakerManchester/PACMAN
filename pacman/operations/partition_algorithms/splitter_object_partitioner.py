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
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.machine import MachineGraph
from pacman.utilities.algorithm_utilities.placer_algorithm_utilities import \
    sort_vertices_by_known_constraints
from pacman.utilities.utility_objs import ResourceTracker
from spinn_utilities.progress_bar import ProgressBar


class SplitterObjectPartitioner(object):
    """ partitioner which hands the partitioning work to app vertices
    splitter objects.

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

    __PROGRESS_BAR_VERTICES = "Partitioning graph vertices"
    __PROGRESS_BAR_EDGES = "Partitioning graph edges"

    __ERROR_MESSAGE_OF_NO_COMMON_EDGE_TYPE = (
        "There was no common edge type between vertex {} and {}. "
        "This means there is no agreed way these 2 vertices can "
        "communicate with each and therefore a machine edge cannot "
        "be created. Please fix and try again")

    __slots__ = []

    # inherited from AbstractPartitionAlgorithm
    def __call__(
            self, app_graph, machine, plan_n_timesteps,
            preallocated_resources=None):
        """
        :param ApplicationGraph app_graph:
        :param ~spinn_machine.Machine machine:
        :param int plan_n_timesteps:
        :param preallocated_resources:
        :type preallocated_resources: PreAllocatedResourceContainer or None
        :rtype: tuple(MachineGraph, int)
        :raise PacmanPartitionException:
        """

        # check resource tracker can handle constraints
        ResourceTracker.check_constraints(app_graph.vertices)

        # get the setup objects
        (machine_graph, resource_tracker, vertices, progress) = (
            self.__setup_objects(
                app_graph, machine, plan_n_timesteps, preallocated_resources))

        # Partition one vertex at a time
        for vertex in progress.over(vertices):
            vertex.splitter_object.split(resource_tracker, machine_graph)

        # process edges
        self.__process_machine_edges(app_graph, machine_graph)

        # return the accepted things
        return machine_graph, resource_tracker.chips_used

    def __setup_objects(
            self, app_graph, machine, plan_n_timesteps,
            preallocated_resources):
        """

        :param ApplicationGraph app_graph: app graph
        :param ~spinn_machine.Machine machine: machine
        :param int plan_n_timesteps: the number of timesteps to run for.
        :param preallocated_resources: pre allocated res from other systems.
        :type PreAllocatedResourceContainer or None
        :return:
        """
        # Load the vertices and create the machine_graph to fill
        machine_graph = MachineGraph(
            label="partitioned graph for {}".format(app_graph.label),
            application_graph=app_graph)

        resource_tracker = ResourceTracker(
            machine, plan_n_timesteps,
            preallocated_resources=preallocated_resources)

        # sort out vertex's by placement constraints
        vertices = sort_vertices_by_known_constraints(app_graph.vertices)

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

    def __process_machine_edges(self, app_graph, machine_graph):
        """ generate the machine edges for the machine graph

        :param ApplicationGraph app_graph: app graph
        :param MachineGraph machine_graph: machine graph
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
                    app_edge.pre_vertex.splitter_object.pre_vertices(
                        app_edge, app_outgoing_edge_partition))

                # go through each pre vertices
                for src_machine_vertex in src_vertices_edge_type_map:
                    dest_vertices_edge_type_map = (
                        app_edge.post_vertex.splitter_object.post_vertices(
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

                        # build edge and add to machine graph
                        machine_edge = common_edge_type(
                            src_machine_vertex, dest_machine_vertex,
                            app_edge=app_edge)
                        machine_graph.add_edge(
                            machine_edge,
                            app_outgoing_edge_partition.identifier)
