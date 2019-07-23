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

"""
test constraint
"""
from pacman.model.constraints.partitioner_constraints import (
    AbstractPartitionerConstraint)


class NewPartitionerConstraint(AbstractPartitionerConstraint):
    """
    a partitioning constraint that shouldn't be recognised by any algorithm
    """

    def __init__(self, label):
        self.label = label

    def is_constraint(self):
        """
        helper method for is_instance

        """
        return True

    def is_partitioner_constraint(self):
        """ Determine if this is a partitioner constraint
        """
        return True
