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


class CoreResource(object):
    """ Represents the number of cores that need to be allocated.
    """

    __slots__ = [

        # The number of cores that need to be allocated on a give chip
        "_n_cores",

        # the chip that has these cores allocated
        "_chip"
    ]

    def __init__(self, chip, n_cores):
        """
        :param int n_cores: The number of cores to allocate
        :param ~spinn_machine.Chip chip:
            chip of where these cores are to be allocated
        """
        self._n_cores = n_cores
        self._chip = chip

    @property
    def n_cores(self):
        return self._n_cores

    @property
    def chip(self):
        return self._chip

    def get_value(self):
        """
        :return: The chip and the cores required on it.
        """
        return self._chip, self._n_cores
