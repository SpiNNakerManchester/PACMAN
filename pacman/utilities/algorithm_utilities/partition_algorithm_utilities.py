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

""" A collection of methods which support partitioning algorithms.
"""
from pacman.model.partitioner_interfaces import HandOverToVertex
from pacman.model.partitioner_interfaces.\
    abstract_controls_destination_of_edges import \
    AbstractControlsDestinationOfEdges
from pacman.model.partitioner_interfaces.\
    abstract_controls_source_of_edges import \
    AbstractControlsSourceOfEdges

try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_set import OrderedSet
from pacman.utilities import utility_calls as utils
from pacman.exceptions import PacmanPartitionException
from pacman.model.constraints.partitioner_constraints import (
    AbstractPartitionerConstraint, SameAtomsAsVertexConstraint,
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint)


def determine_max_atoms_for_vertex(vertex):
    """  returns the max atom constraint after assessing them all.

    :param vertex: the vertex to find max atoms of
    :return: the max number of atoms per core
    """
    possible_max_atoms = list()
    n_atoms = None
    max_atom_constraints = utils.locate_constraints_of_type(
        vertex.constraints, MaxVertexAtomsConstraint)
    for constraint in max_atom_constraints:
        possible_max_atoms.append(constraint.size)
    n_atom_constraints = utils.locate_constraints_of_type(
        vertex.constraints, FixedVertexAtomsConstraint)
    for constraint in n_atom_constraints:
        if n_atoms is not None and constraint.size != n_atoms:
            raise PacmanPartitionException(
                "Vertex has multiple contradictory fixed atom "
                "constraints - cannot be both {} and {}".format(
                    n_atoms, constraint.size))
        n_atoms = constraint.size
    if len(possible_max_atoms) != 0:
        return int(min(possible_max_atoms))
    else:
        return vertex.n_atoms


def _process_edge(
        app_edge, machine_graph, graph_mapper, application_partition,
        original_source_machine_vertex):
    # get destinations
    if isinstance(app_edge.post_vertex, AbstractControlsDestinationOfEdges):
        dest_vertices = app_edge.post_vertex.get_destinations_for_edge_from(
            app_edge, application_partition, graph_mapper,
            original_source_machine_vertex)
    else:
        dest_vertices = graph_mapper.get_machine_vertices(app_edge.post_vertex)

    # get sources
    if isinstance(app_edge.pre_vertex, AbstractControlsSourceOfEdges):
        source_vertices = app_edge.pre_vertex.get_sources_for_edge_from(
            app_edge, application_partition, graph_mapper,
            original_source_machine_vertex)
    else:
        source_vertices = [original_source_machine_vertex]

    # build and update objects
    for dest_vertex in dest_vertices:
        for source_vertex in source_vertices:
            # create new partitions
            machine_edge = app_edge.create_machine_edge(
                source_vertex, dest_vertex,
                "machine_edge_for{}".format(app_edge.label))
            machine_graph.add_edge(
                machine_edge, application_partition.identifier)

            # add constraints from the application partition
            machine_partition = machine_graph.\
                get_outgoing_edge_partition_starting_at_vertex(
                    source_vertex, application_partition.identifier)
            machine_partition.add_constraints(
                application_partition.constraints)

            # update mapping object
            graph_mapper.add_edge_mapping(machine_edge, app_edge)


def generate_machine_edges(machine_graph, graph_mapper, application_graph):
    """ Generate the machine edges for the vertices in the graph

    :param MachineGraph machine_graph: the machine graph to add edges to
    :param GraphMapper graph_mapper: the mapper graphs
    :param ApplicationGraph application_graph:
        the application graph to work with
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
                _process_edge(
                    application_edge, machine_graph, graph_mapper,
                    application_partition, source_vertex)


def get_remaining_constraints(vertex):
    """ Gets the rest of the constraints from a vertex after removing\
        partitioning constraints.

    :param ApplicationVertex vertex:
    :rtype: list(AbstractConstraint)
    """
    return [constraint for constraint in vertex.constraints
            if not isinstance(constraint, AbstractPartitionerConstraint)]


def get_same_size_vertex_groups(vertices):
    """ Get a dictionary of vertex to vertex that must be partitioned the same\
        size.

    :param iterble(ApplicationVertex) vertices:
    :rtype: dict(ApplicationVertex, set(ApplicationVertex))
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
                if isinstance(constraint.vertex, HandOverToVertex):
                    raise PacmanPartitionException(
                        "Vertex {} cannot handle being partitioned "
                        "alongside vertex {}. Pleas efix and try "
                        "again".format(vertex, constraint.vertex)
                    )
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
