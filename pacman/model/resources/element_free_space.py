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


class ElementFreeSpace(object):
    """ Describes a contiguous chunk of free space managed by an allocator \
        algorithm.
    """

    __slots__ = ["_size", "_start_address"]

    def __init__(self, start_address, size):
        """
        :param int start_address: Where the space starts
        :param int size: The number of items (bytes, etc.) in the space
        """
        self._start_address = start_address
        self._size = size

    @property
    def start_address(self):
        """
        :rtype: int
        """
        return self._start_address

    @property
    def size(self):
        """
        :rtype: int
        """
        return self._size

    def __repr__(self):
        return "ElementFreeSpace:start={}:size={}".format(
            hex(self._start_address), self._size)

    def __str__(self):
        return self.__repr__()
