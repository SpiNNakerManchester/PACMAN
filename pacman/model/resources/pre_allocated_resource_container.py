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

from pacman.exceptions import PacmanConfigurationException


class PreAllocatedResourceContainer(object):
    """ Container object for preallocated resources
    """

    __slots__ = [
        # An iterable of SpecificSDRAMResource object that reflects the amount
        # of SDRAM (in bytes) preallocated on a specific chip on the SpiNNaker
        #  machine
        "_specific_sdram_usage",

        # An iterable of SpecificCoreResource objects that reflect the number
        # of specific cores that have been preallocated on a chip.
        "_specific_core_resources",

        # An iterable of CoreResource objects that reflect the number of
        # cores that have been preallocated on a chip, but which don't care
        # which core it uses.
        "_core_resources",

        # An iterable of SpecificIPTagResource objects that reflect the IP tag
        # details that have been preallocated on a board.
        "_specific_iptag_resources",

        # An iterable of SpecificReverseIPTagResource objects that reflect the
        # reverse IP tag details that have been preallocated on a board.
        "_specific_reverse_iptag_resources",
    ]

    def __init__(
            self, specific_sdram_usage=None, specific_core_resources=None,
            core_resources=None, specific_iptag_resources=None,
            specific_reverse_iptag_resources=None):
        """
        :param iterable(SpecificChipSDRAMResource) specific_sdram_usage:
            iterable of SpecificSDRAMResource which states that specific chips
            have missing SDRAM
        :param iterable(SpecificCoreResource) specific_core_resources:
            states which cores have been preallocated
        :param iterable(CoreResource) core_resources:
            states a number of cores have been preallocated but don't care
            which ones they are
        :param list(SpecificBoardTagResource) specific_iptag_resources:
        :param list(SpecificReverseIPTagResource) \
                specific_reverse_iptag_resources:
        """
        # pylint: disable=too-many-arguments
        self._specific_sdram_usage = specific_sdram_usage
        self._specific_core_resources = specific_core_resources
        self._core_resources = core_resources
        self._specific_iptag_resources = specific_iptag_resources
        self._specific_reverse_iptag_resources = \
            specific_reverse_iptag_resources

        # check for none resources
        if self._specific_sdram_usage is None:
            self._specific_sdram_usage = []
        if self._specific_core_resources is None:
            self._specific_core_resources = []
        if self._core_resources is None:
            self._core_resources = []
        if self._specific_iptag_resources is None:
            self._specific_iptag_resources = []
        if self._specific_reverse_iptag_resources is None:
            self._specific_reverse_iptag_resources = []

    @property
    def specific_sdram_usage(self):
        return self._specific_sdram_usage

    @property
    def specific_core_resources(self):
        return self._specific_core_resources

    @property
    def core_resources(self):
        return self._core_resources

    @property
    def specific_iptag_resources(self):
        return self._specific_iptag_resources

    @property
    def specific_reverse_iptag_resources(self):
        return self._specific_reverse_iptag_resources

    def extend(self, other):
        """
        :param PreAllocatedResourceContainer other:
        """
        if not isinstance(other, PreAllocatedResourceContainer):
            raise PacmanConfigurationException(
                "Only another preallocated resource container can extend a "
                "preallocated resource container")

        # add specific SDRAM usage
        self._specific_sdram_usage.extend(other.specific_sdram_usage)

        # add specific cores
        self._specific_core_resources.extend(other.specific_core_resources)

        # add non-specific cores
        self._core_resources.extend(other.core_resources)

        # add IP tag resources
        self._specific_iptag_resources.extend(other.specific_iptag_resources)

        # add reverse IP tag resources
        self._specific_reverse_iptag_resources.extend(
            other.specific_reverse_iptag_resources)
