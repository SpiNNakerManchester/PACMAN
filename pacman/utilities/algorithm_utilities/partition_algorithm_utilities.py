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

import math
from collections import OrderedDict
from spinn_utilities.ordered_set import OrderedSet
from pacman.utilities import utility_calls as utils
from pacman.exceptions import (
    PacmanPartitionException, PacmanConfigurationException)
from pacman.model.constraints.partitioner_constraints import (
    AbstractPartitionerConstraint, SameAtomsAsVertexConstraint,
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint)
from pacman.model.graphs.common import Slice


VERTICES_NEED_TO_BE_SAME_SIZE_ERROR = (
    "Vertices {} ({} atoms) and {} ({} atoms) must be of the same size to"
    " partition them together")

CONTRADICTORY_FIXED_ATOM_ERROR = (
    "Vertex has multiple contradictory fixed atom constraints - cannot"
    " be both {} and {}")


def determine_max_atoms_for_vertex(vertex):
    """  returns the max atom constraint after assessing them all.

    :param ApplicationVertex vertex: the vertex to find max atoms of
    :return: the max number of atoms per core
    :rtype: int
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
                CONTRADICTORY_FIXED_ATOM_ERROR.format(
                    n_atoms, constraint.size))
        n_atoms = constraint.size
    if len(possible_max_atoms) != 0:
        return int(min(possible_max_atoms))
    else:
        return vertex.n_atoms


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
                        VERTICES_NEED_TO_BE_SAME_SIZE_ERROR.format(
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


def get_multidimensional_slices(n_atoms, atoms_per_core):
    if isinstance(atoms_per_core, int):
        atoms_per_core = [atoms_per_core] * len(n_atoms)
    while len(atoms_per_core) != len(n_atoms):
        raise PacmanConfigurationException(
            "The length of atoms_per_core doesn't match the number of"
            " dimensions")

    # Find out how many vertices we will create, keeping track of the
    # total atoms per core, and the numerator to divide by when working
    # out positions
    n_vertices = 1
    total_atoms_per_core = 1
    dim_numerator = [0] * len(n_atoms)
    total_n_atoms = 1
    for d in range(len(n_atoms)):
        dim_numerator[d] = n_vertices
        n_this_dim = int(math.ceil(n_atoms[d] / atoms_per_core[d]))
        n_vertices *= n_this_dim
        total_atoms_per_core *= atoms_per_core[d]
        total_n_atoms *= n_atoms[d]

    # Run over all the vertices and create slices for them
    slices = list()
    hi_atom = -1
    for v in range(n_vertices):
        # Work out where in each of the dimensions this vertex starts by
        # dividing the remainder from the previous dimension by the
        # numerator of each dimension
        start = [0] * len(n_atoms)
        n_on_core = [0] * len(n_atoms)
        remainder = v
        total_on_core = 1
        for d in reversed(range(len(n_atoms))):
            start[d] = (remainder // dim_numerator[d]) * atoms_per_core[d]
            remainder = remainder % dim_numerator[d]
            hi_d = min(start[d] + atoms_per_core[d], n_atoms[d])
            n_on_core[d] = hi_d - start[d]
            total_on_core *= n_on_core[d]

        # Make a slice and a vertex
        lo_atom = hi_atom + 1
        hi_atom = (lo_atom + total_on_core) - 1
        vertex_slice = Slice(
            lo_atom, hi_atom, tuple(n_on_core), tuple(start))
        slices.append(vertex_slice)

    return slices
