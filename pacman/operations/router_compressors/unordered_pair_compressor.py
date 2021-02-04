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

from .pair_compressor import PairCompressor


class UnorderedPairCompressor(PairCompressor):
    """
    A version of the pair compressor that does not consider order or length

    The resulting entries are unordered,
    which allows the use of a second follow on compressor.

    The results are not checked for length so the results may be too big to be
    used unless compressed again.
    """
    def __init__(self):
        super().__init__(False)
