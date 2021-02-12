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

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import PacmanInvalidParameterException
from pacman.model.constraints import AbstractConstraint


def _get_class_name(cls):
    return "{}.{}".format(cls.__module__, cls.__name__)


class ConstrainedObject(object, metaclass=AbstractBase):
    """ An implementation of an object which holds constraints.
    """

    __slots__ = [
        # The constraints of the object
        "_constraints"
    ]

    def __init__(self, constraints=None):
        """
        :param iterable(AbstractConstraint) constraints:
            Any initial constraints
        """

        # safety point for diamond inheritance
        if not hasattr(self, '_constraints') or self._constraints is None:
            self._constraints = OrderedSet()

        # add new constraints to the set
        self.add_constraints(constraints)

    def add_constraint(self, constraint):
        """ Add a new constraint to the collection of constraints.

        :param AbstractConstraint constraint: constraint to add
        :raise PacmanInvalidParameterException:
            If the constraint is not valid
        """
        if constraint is None:
            raise PacmanInvalidParameterException(
                "constraint", constraint, "must not be None")
        if not isinstance(constraint, AbstractConstraint):
            raise PacmanInvalidParameterException(
                "constraint", constraint,
                "Must be a " + _get_class_name(AbstractConstraint))

        try:
            self._constraints.add(constraint)
        except Exception:  # pylint: disable=broad-except
            self._constraints = OrderedSet()
            self._constraints.add(constraint)

    def add_constraints(self, constraints):
        """ Add an iterable of constraints to the collection of constraints.

        :param AbstractConstraint constraints: the constraints to add
        :raise PacmanInvalidParameterException:
            If one of the constraints is not valid
        """
        if constraints is not None:
            for next_constraint in constraints:
                self.add_constraint(next_constraint)

    @property
    def constraints(self):
        """ An iterable of constraints

        :rtype: iterable(AbstractConstraint)
        """
        try:
            return self._constraints
        except Exception:  # pylint: disable=broad-except
            return OrderedSet()
