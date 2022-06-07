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

from pacman.model.constraints.partitioner_constraints import (
    AbstractPartitionerConstraint)


VERTICES_NEED_TO_BE_SAME_SIZE_ERROR = (
    "Vertices {} ({} atoms) and {} ({} atoms) must be of the same size to"
    " partition them together")

CONTRADICTORY_FIXED_ATOM_ERROR = (
    "Vertex has multiple contradictory fixed atom constraints - cannot"
    " be both {} and {}")


def get_remaining_constraints(vertex):
    """ Gets the rest of the constraints from a vertex after removing\
        partitioning constraints.

    :param ApplicationVertex vertex:
    :rtype: list(AbstractConstraint)
    """
    return [constraint for constraint in vertex.constraints
            if not isinstance(constraint, AbstractPartitionerConstraint)]
