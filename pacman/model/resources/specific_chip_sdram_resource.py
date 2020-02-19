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

from pacman.model.resources import AbstractSDRAM


class SpecificChipSDRAMResource(object):
    """ Represents the SDRAM required for this Chip
    """

    __slots__ = [

        # The number of cores that need to be allocated on a give chip
        "_sdram_usage",

        # the chip that has this SDRAM usage
        "_chip"
    ]

    def __init__(self, chip, sdram_usage):
        """
        :param AbstractSDRAM sdram_usage:
            The amount of SDRAM in bytes needed to be preallocated
        :param ~spinn_machine.Chip chip:
            chip of where the SDRAM is to be allocated
        """
        assert isinstance(sdram_usage, AbstractSDRAM)
        self._sdram_usage = sdram_usage
        self._chip = chip

    @property
    def sdram_usage(self):
        """
        :rtype: AbstractSDRAM
        """
        return self._sdram_usage

    @property
    def chip(self):
        """
        :rtype: ~spinn_machine.Chip
        """
        return self._chip

    def get_value(self):
        """
        :return: The chip for which it is required, and the amount of SDRAM\
            required thereon, in bytes.
        :rtype: tuple(~spinn_machine.Chip, AbstractSDRAM)
        """
        return self._chip, self._sdram_usage
