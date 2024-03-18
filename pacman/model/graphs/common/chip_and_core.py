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
from typing import Optional


class ChipAndCore(object):
    """
    A constraint to place a vertex on a specific chip and, optionally, a
    specific core on that chip.
    """

    __slots__ = (
        # the chip coordinates in the SpiNNaker machine to which the machine
        # vertex is placed
        "_x", "_y",
        # The processor ID on chip (x,y) that this vertex is placed on within
        # the SpiNNaker machine; may be None
        "_p")

    def __init__(self, x: int, y: int, p: Optional[int] = None):
        """
        :param int x: the x-coordinate of the chip
        :param int y: the y-coordinate of the chip
        :param p: the processor (if any) of the chip
        :type p: int or None
        """
        self._x = int(x)
        self._y = int(y)
        self._p = None if p is None else int(p)

    @property
    def x(self) -> int:
        """
        The X-coordinate of the chip.

        :rtype: int
        """
        return self._x

    @property
    def y(self) -> int:
        """
        The Y-coordinate of the chip.

        :rtype: int
        """
        return self._y

    @property
    def p(self) -> Optional[int]:
        """
        The processor on the chip, or `None` if that is not constrained.

        :rtype: int or None
        """
        return self._p

    def __repr__(self) -> str:
        if self._p is None:
            return f"X:{self._x},Y{self._y}"
        else:
            return f"X:{self._x},Y:{self._y},P:{self._p}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, ChipAndCore):
            return False
        return (self._x, self._y, self._p) == (other.x, other.y, other.p)

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self._x, self._y, self._p))
