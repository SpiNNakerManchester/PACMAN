"""
A collection of methods which support partitioning algorithms.
"""

import logging

from pacman.model.constraints.partitioner_constraints\
    .abstract_partitioner_constraint import AbstractPartitionerConstraint
from spinn_machine.utilities.progress_bar import ProgressBar

logger = logging.getLogger(__name__)


def generate_machine_edges(machine_graph, graph_mapper, graph):
    """ Generate the machine edges for the vertices in the graph

    :param machine_graph: the machine graph to add edges to
    :type machine_graph:\
        :py:class:`pacman.model.graph.machine.machine_graph.MachineGraph`
    :param graph_mapper: the mapper graphs
    :type graph_mapper:\
        :py:class:`pacman.model.graph_mapper.GraphMapper`
    :param graph: the application graph to work with
    :type graph:\
        :py:class:`pacman.model.graph.application.application_graph.ApplicationGraph`
    """

    # start progress bar
    progress_bar = ProgressBar(len(machine_graph.vertices),
                               "Partitioning graph edges")

    # Partition edges according to vertex partitioning
    for source_vertex in machine_graph.vertices:

        # For each out edge of the parent vertex...
        vertex = graph_mapper.get_application_vertex(source_vertex)
        outgoing_partitions = \
            graph.get_outgoing_edge_partitions_starting_at_vertex(vertex)
        for partition in outgoing_partitions:
            out_edges = partition.edges
            for edge in out_edges:

                # and create and store a new edge for each post-vertex
                post_vertex = edge.post_vertex
                post_vertices = graph_mapper.get_machine_vertices(post_vertex)
                for dest_vertex in post_vertices:
                    machine_edge = edge.create_machine_edge(
                        source_vertex, dest_vertex)
                    machine_graph.add_edge(machine_edge, partition.identifier)
                    graph_mapper.add_edge_mapping(
                        machine_edge, edge)
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
