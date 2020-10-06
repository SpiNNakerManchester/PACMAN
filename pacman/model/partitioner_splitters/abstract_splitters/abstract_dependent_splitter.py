# Copyright (c) 2020-2021 The University of Manchester
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
from pacman.model.partitioner_interfaces import AbstractSplitterCommon


class AbstractDependentSplitter(AbstractSplitterCommon):
    """ splitter that works on slices from another splitter.

    """

    __slots__ = [
        "_other_splitter"
    ]

    def __init__(self, other_splitter, splitter_name):
        AbstractSplitterCommon.__init__(self, splitter_name)
        self._other_splitter = other_splitter

    @property
    def other_splitter(self):
        return self._other_splitter
