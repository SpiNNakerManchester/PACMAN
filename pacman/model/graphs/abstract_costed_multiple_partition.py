# Copyright (c) 2019-2020 The University of Manchester
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

from six import add_metaclass

from pacman.model.graphs import AbstractMultiplePartition
from spinn_utilities.abstract_base import AbstractBase


@add_metaclass(AbstractBase)
class AbstractCostedMultiplePartition(AbstractMultiplePartition):
    """ needed for future proofing against other types of costed partitions.
    """

    __slots__ = ["_allocated"]

    def __init__(
            self, pre_vertices, identifier, allowed_edge_types, constraints,
            label, traffic_weight, class_name, traffic_type):
        super(AbstractCostedMultiplePartition, self).__init__(
            pre_vertices, identifier, allowed_edge_types, constraints,
            label, traffic_weight, class_name, traffic_type)
        self._allocated = False

    @property
    def allocated(self):
        return self._allocated

    @allocated.setter
    def allocated(self, new_value):
        self._allocated = new_value
