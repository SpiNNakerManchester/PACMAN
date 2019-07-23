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


class MinimisationFailedError(Exception):
    """Raised when a routing table could not be minimised to reach a specified
    target.

    Attributes
    ----------
    target_length : int
        The target number of routing entries.
    final_length : int
        The number of routing entries reached when the algorithm completed.
        (final_length > target_length)
    chip : (x, y) or None
        The coordinates of the chip on which routing table minimisation first
        failed. Only set when minimisation is performed across many chips
        simultaneously.
    """

    def __init__(self, target_length, final_length=None, chip=None):
        self.chip = chip
        self.target_length = target_length
        self.final_length = final_length

    def __str__(self):
        if self.chip is not None:
            x, y = self.chip
            text = ("Could not minimise routing table for "
                    "({}, {}) ".format(x, y))
        else:
            text = "Could not minimise routing table "

        text += "to fit in {} entries.".format(self.target_length)

        if self.final_length is not None:
            text += " Best managed was {} entries.".format(self.final_length)

        return text
