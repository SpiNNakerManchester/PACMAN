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
based on
https://github.com/project-rig/rig/blob/master/rig/routing_table/utils.py
"""


def intersect(key_a, mask_a, key_b, mask_b):
    """Return if key-mask pairs intersect (i.e., would both match some of the
    same keys).

    For example, the key-mask pairs ``00XX`` and ``001X`` both match the keys
    ``0010`` and ``0011`` (i.e., they do intersect)::

        >>> intersect(0b0000, 0b1100, 0b0010, 0b1110)
        True

    But the key-mask pairs ``00XX`` and ``11XX`` do not match any of the same
    keys (i.e., they do not intersect)::

        >>> intersect(0b0000, 0b1100, 0b1100, 0b1100)
        False

    :param int key_a:
    :param int mask_a: The first key-mask pair
    :param int key_b:
    :param int mask_b: The second key-mask pair
    :rtype: bool
    :return: True if the two key-mask pairs intersect, otherwise False.
    """
    return (key_a & mask_b) == (key_b & mask_a)
