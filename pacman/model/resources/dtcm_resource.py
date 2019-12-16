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


class DTCMResource(object):
    """ Represents the amount of local core memory available or used on a core\
        on a chip of the machine.
    """

    __slots__ = [

        # The number of DTCM (in bytes) needed for a given object
        "_dtcm"
    ]

    def __init__(self, dtcm):
        """
        :param int dtcm: The amount of DTCM in bytes
        """
        self._dtcm = dtcm

    def get_value(self):
        """
        :return: The required amount of DTCM, in bytes.
        :rtype: int
        """
        return self._dtcm
