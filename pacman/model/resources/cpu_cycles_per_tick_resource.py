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


class CPUCyclesPerTickResource(object):
    """ Represents the number of CPU clock cycles per tick used or available\
        on a core of a chip in the machine.
    """

    __slots__ = [

        # The number of CPU cycles needed for a given object
        "_cycles"
    ]

    def __init__(self, cycles):
        """
        :param int cycles: The number of CPU clock cycles
        """
        self._cycles = cycles

    def get_value(self):
        """
        :return: The number of CPU clock cycles needed per simulation tick.
        """
        return self._cycles
