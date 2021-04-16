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
This is a package of algorithms that originated in Rig.

Converted to PACMAN by Sara Summerton.
"""

from .hilbert_placer import HilbertPlacer
from .hilbert_state import HilbertState
from .random_placer import RandomPlacer

__all__ = [
    "HilbertPlacer", "HilbertState", "RandomPlacer"]
