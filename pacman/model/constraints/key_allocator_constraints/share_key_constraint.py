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

from .abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint


class ShareKeyConstraint(AbstractKeyAllocatorConstraint):
    """ Constraint to allow the same keys to be allocated to multiple edges\
        via partitions.
    """

    __slots__ = [
        # The set of outgoing partitions to vertices which all share the same\
        # key
        "_other_partitions"
    ]

    def __init__(self, other_partitions):
        """
        :param other_partitions: the other edges which keys are shared with.
        """
        self._other_partitions = other_partitions

    @property
    def other_partitions(self):
        return self._other_partitions
