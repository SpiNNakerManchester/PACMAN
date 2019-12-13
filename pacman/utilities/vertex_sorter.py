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

import sys
from six import itervalues
from spinn_utilities.ordered_default_dict import DefaultOrderedDict


class ConstraintOrder(object):
    """ A constraint order definition for sorting.
    """

    __slots__ = [
        # The class of the constraint
        "_constraint_class",

        # The order of the constraint relative to other constraints to be
        #  sorted
        "_relative_order",

        # Properties of the constraint instances that must not be None for
        # the constraint to match this ordering
        "_required_optional_properties"
    ]

    def __init__(
            self, constraint_class, relative_order,
            required_optional_properties=None):
        """
        :param type constraint_class: The class of the constraint
        :param int relative_order:
            The order of the constraint relative to other constraints to be\
            sorted
        :param required_optional_properties:
            Properties of the constraint instances that must not be None for\
            the constraint to match this ordering
        :type required_optional_properties: list(str) or None
        """
        self._constraint_class = constraint_class
        self._relative_order = relative_order
        self._required_optional_properties = required_optional_properties

    @property
    def constraint_class(self):
        """ the constraint class

        :rtype: type
        """
        return self._constraint_class

    @property
    def relative_order(self):
        """ the relative order

        :rtype: int
        """
        return self._relative_order

    @property
    def required_optional_properties(self):
        """ the required optional properties

        :rtype: list(str) or None
        """
        return self._required_optional_properties


class VertexSorter(object):
    """ Sorts vertices based on constraints with given criteria.
    """

    __slots__ = [
        # Group constraints based on the class
        "_constraints"
    ]

    def __init__(self, constraint_order):
        """
        :param list(~.ConstraintOrder) constraint_order:
            The order in which the constraints are to be sorted
        """
        # Group constraints based on the class
        self._constraints = DefaultOrderedDict(list)
        for c in constraint_order:
            self._constraints[c.constraint_class].append(
                (c.relative_order, c.required_optional_properties))

        # Sort each list of constraint by the number of optional properties,
        # largest first
        for constraints in itervalues(self._constraints):
            constraints.sort(key=len, reverse=True)

    def sort(self, vertices):
        """ Sort the given set of vertices by the constraint ordering

        :param list(AbstractVertex) vertices: The vertices to sort
        :return: The sorted list of vertices
        :rtype: list(AbstractVertex)
        """
        vertices_with_rank = list()
        for vertex in vertices:

            # Get all the ranks of the constraints
            ranks = [sys.maxsize]
            for c in vertex.constraints:

                # If the constraint is one to sort by
                if c.__class__ in self._constraints:
                    current_ranks = self._constraints[c.__class__]
                    for (rank, required_param) in current_ranks:
                        if self._matches(c, required_param):
                            ranks.append(rank)

            # Sort and store the ranks for overall ordering
            ranks.sort()
            vertices_with_rank.append((vertex, ranks))

        # Sort the vertices - because ranks is a list, things with the same
        # min rank will be sorted by the next highest rank and so on
        vertices_with_rank.sort(key=lambda thing: thing[1])
        # Strip the ranks from the sorted list
        return [vertex for vertex, _ in vertices_with_rank]

    @staticmethod
    def _matches(constraint, opts):
        """ Determines if the constraint matches the given optional required\
            parameters

        :param AbstractConstraint constraint:
        :param opts:
        :type opts: list(str) or None
        :rtype: bool
        """
        if opts is None:
            return True
        return all(getattr(constraint, opt) is not None
                   for opt in opts)
