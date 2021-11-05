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

from pacman.utilities import utility_calls as utils
from pacman.exceptions import PacmanPartitionException
from pacman.model.constraints.partitioner_constraints import (
    AbstractPartitionerConstraint, MaxVertexAtomsConstraint,
    FixedVertexAtomsConstraint)


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
