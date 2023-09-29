# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
based on
https://github.com/project-rig/rig/blob/master/rig/routing_table/utils.py
"""


def intersect(key_a, mask_a, key_b, mask_b):
    """
    Return if key-mask pairs intersect (i.e., would both match some of the
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
