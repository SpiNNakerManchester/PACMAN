"""
A collection of methods which support partitioning algorithms.
"""

import logging

from pacman.model.constraints.partitioner_constraints\
    .abstract_partitioner_constraint import AbstractPartitionerConstraint
from spinn_machine.utilities.progress_bar import ProgressBar

logger = logging.getLogger(__name__)


def generate_machine_edges(machine_graph, graph_mapper, application_graph):
    """ Generate the machine edges for the vertices in the graph

    :param machine_graph: the machine graph to add edges to
    :type machine_graph:\
        :py:class:`pacman.model.graph.machine.machine_graph.MachineGraph`
    :param graph_mapper: the mapper graphs
    :type graph_mapper:\
        :py:class:`pacman.model.graph_mapper.GraphMapper`
    :param application_graph: the application graph to work with
    :type application_graph:\
        :py:class:`pacman.model.graph.application.application_graph.ApplicationGraph`
    """

    # start progress bar
    progress_bar = ProgressBar(
        machine_graph.n_vertices, "Partitioning graph edges")

    # Partition edges according to vertex partitioning
    for source_vertex in machine_graph.vertices:

        # For each out edge of the parent vertex...
        vertex = graph_mapper.get_application_vertex(source_vertex)
        application_outgoing_partitions = application_graph.\
            get_outgoing_edge_partitions_starting_at_vertex(vertex)
        for application_partition in application_outgoing_partitions:
            for application_edge in application_partition.edges:

                # and create and store a new edge for each post-vertex
                application_post_vertex = application_edge.post_vertex
                machine_post_vertices = \
                    graph_mapper.get_machine_vertices(application_post_vertex)

                # create new partitions
                for machine_dest_vertex in machine_post_vertices:
                    machine_edge = application_edge.create_machine_edge(
                        source_vertex, machine_dest_vertex,
                        "machine_edge_for{}".format(application_edge.label))
                    machine_graph.add_edge(
                        machine_edge, application_partition.identifier)

                    # add constraints from the application partition
                    machine_partition = machine_graph.\
                        get_outgoing_edge_partition_starting_at_vertex(
                            source_vertex, application_partition.identifier)
                    machine_partition.add_constraints(
                        application_partition.constraints)

                    # update mapping object
                    graph_mapper.add_edge_mapping(
                        machine_edge, application_edge)
        progress_bar.update()
    progress_bar.end()


def get_remaining_constraints(vertex):
    """ Gets the rest of the constraints from a vertex after removing\
        partitioning constraints
    """
    constraints = list()
    for constraint in vertex.constraints:
        if not isinstance(constraint, AbstractPartitionerConstraint):
            constraints.append(constraint)
    return constraints
