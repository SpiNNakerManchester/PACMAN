""" A collection of methods which support partitioning algorithms.
"""
try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import PacmanPartitionException
from pacman.model.constraints.partitioner_constraints import (
    AbstractPartitionerConstraint, SameAtomsAsVertexConstraint)
from spinnak_ear.IHCAN_vertex import IHCANVertex
from spinnak_ear.spinnakear_vertex import SpiNNakEarVertex
from spinnak_ear.DRNL_vertex import DRNLVertex
from spinnak_ear.AN_group_vertex import ANGroupVertex

def generate_machine_edges(machine_graph, graph_mapper, application_graph):
    """ Generate the machine edges for the vertices in the graph

    :param machine_graph: the machine graph to add edges to
    :type machine_graph:\
        :py:class:`pacman.model.graphs.machine.MachineGraph`
    :param graph_mapper: the mapper graphs
    :type graph_mapper:\
        :py:class:`pacman.model.graphs.common.GraphMapper`
    :param application_graph: the application graph to work with
    :type application_graph:\
        :py:class:`pacman.model.graphs.application.ApplicationGraph`
    """

    # start progress bar
    progress = ProgressBar(
        machine_graph.n_vertices, "Partitioning graph edges")

    # Partition edges according to vertex partitioning
    for source_vertex in progress.over(machine_graph.vertices):

        # For each out edge of the parent vertex...
        vertex = graph_mapper.get_application_vertex(source_vertex)
        application_outgoing_partitions = application_graph.\
            get_outgoing_edge_partitions_starting_at_vertex(vertex)
        for application_partition in application_outgoing_partitions:
            for application_edge in application_partition.edges:
                # create new partitions
                for dest_vertex in graph_mapper.get_machine_vertices(
                        application_edge.post_vertex):
                    if (not isinstance(application_edge.post_vertex, SpiNNakEarVertex) \
                        and not isinstance(application_edge.pre_vertex, SpiNNakEarVertex))\
                        or isinstance(dest_vertex,DRNLVertex) or (isinstance(source_vertex,ANGroupVertex)
                    and source_vertex._is_final_row == True):
                        machine_edge = application_edge.create_machine_edge(
                            source_vertex, dest_vertex,
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


def get_remaining_constraints(vertex):
    """ Gets the rest of the constraints from a vertex after removing\
        partitioning constraints
    """
    return [constraint for constraint in vertex.constraints
            if not isinstance(constraint, AbstractPartitionerConstraint)]


def get_same_size_vertex_groups(vertices):
    """ Get a dictionary of vertex to vertex that must be partitioned the same\
        size
    """

    # Dict of vertex to list of vertices with same size
    # (repeated lists expected)
    same_size_vertices = OrderedDict()

    for vertex in vertices:

        # Find all vertices that have a same size constraint associated with
        #  this vertex
        same_size_as_vertices = list()
        for constraint in vertex.constraints:
            if isinstance(constraint, SameAtomsAsVertexConstraint):
                if vertex.n_atoms != constraint.vertex.n_atoms:
                    raise PacmanPartitionException(
                        "Vertices {} ({} atoms) and {} ({} atoms) must be of"
                        " the same size to partition them together".format(
                            vertex.label, vertex.n_atoms,
                            constraint.vertex.label,
                            constraint.vertex.n_atoms))
                same_size_as_vertices.append(constraint.vertex)

        if not same_size_as_vertices:
            same_size_vertices[vertex] = {vertex}
            continue

        # Go through all the vertices that want to have the same size
        # as the top level vertex
        for same_size_vertex in same_size_as_vertices:

            # Neither vertex has been seen
            if (same_size_vertex not in same_size_vertices and
                    vertex not in same_size_vertices):

                # add both to a new group
                group = OrderedSet([vertex, same_size_vertex])
                same_size_vertices[vertex] = group
                same_size_vertices[same_size_vertex] = group

            # Both vertices have been seen elsewhere
            elif (same_size_vertex in same_size_vertices and
                    vertex in same_size_vertices):

                # merge their groups
                group_1 = same_size_vertices[vertex]
                group_2 = same_size_vertices[same_size_vertex]
                group_1.update(group_2)
                for vert in group_1:
                    same_size_vertices[vert] = group_1

            # The current vertex has been seen elsewhere
            elif vertex in same_size_vertices:

                # add the new vertex to the existing group
                group = same_size_vertices[vertex]
                group.add(same_size_vertex)
                same_size_vertices[same_size_vertex] = group

            # The other vertex has been seen elsewhere
            elif same_size_vertex in same_size_vertices:

                #  so add this vertex to the existing group
                group = same_size_vertices[same_size_vertex]
                group.add(vertex)
                same_size_vertices[vertex] = group

    return same_size_vertices
