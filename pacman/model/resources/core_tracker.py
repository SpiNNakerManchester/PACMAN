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

from spinn_utilities.ordered_set import OrderedSet
from spinn_machine import Machine


class CoreTracker(object):
    """ Represents the number of cores and sdram left to allocate
    """

    __slots__ = [

        # The number of cores available after preallocation
        "_n_cores",

        # cores available including ones needed for preallocation
        "_cores",

        # keep list of counts of the cores per n_cores_available
        "_cores_counter",
    ]

    def __init__(self, chip, preallocated_resources, cores_counter):
        """
        :param ~spinn_machine.Chip chip:
            chip whose resources can be allocated
        :param preallocated_resources:
        :type preallocated_resources: PreAllocatedResourceContainer or None
        """
        global _real_chips_with_n_cores_available
        self._cores = OrderedSet()
        for processor in chip.processors:
            if not processor.is_monitor:
                self._cores.add(processor.processor_id)
        self._n_cores = len(self._cores)
        if preallocated_resources:
            if chip.ip_address:
                self._n_cores -= preallocated_resources.cores_ethernet
            else:
                self._n_cores -= preallocated_resources.cores_all
        if chip.virtual:
            self._cores_counter = None
        else:
            self._cores_counter = cores_counter
        if self._cores_counter:
            self._cores_counter[self._n_cores] += 1

    @property
    def n_cores_available(self):
        return self._n_cores

    def is_core_available(self, p):
        if p is None:
            return self.is_available
        else:
            return p in self._cores

    def available_core(self):
        return self._cores.peek()

    @property
    def is_available(self):
        return self._n_cores > 0

    def allocate(self, p):
        global _real_chips_with_n_cores_available
        if p is None:
            p = self._cores.pop()
        else:
            self._cores.remove(p)
        if self._cores_counter:
            self._cores_counter[self._n_cores] -= 1
        self._n_cores -= 1
        if self._cores_counter:
            self._cores_counter[self._n_cores] += 1

        if self._n_cores <= 0:
            self._cores = OrderedSet()
        return p

    def deallocate(self, p):
        self._cores.add(p)
        if self._cores_counter:
            self._cores_counter[self._n_cores] -= 1
        self._n_cores += 1
        if self._cores_counter:
            self._cores_counter[self._n_cores] += 1
