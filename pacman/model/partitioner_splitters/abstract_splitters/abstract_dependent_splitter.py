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

from .abstract_splitter_common import AbstractSplitterCommon
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanPartitionException)


class AbstractDependentSplitter(AbstractSplitterCommon):
    """ splitter that defines it needs to be run after another splitter.

    """

    __slots__ = [
        "_other_splitter"
    ]

    def __init__(self, other_splitter, splitter_name):
        """
        Creates a splitter that must be done after the other unless None.

        :param other_splitter:
        :type other_splitter: AbstractSplitterCommon or None
        :param splitter_name:
        """
        AbstractSplitterCommon.__init__(self, splitter_name)
        self._other_splitter = other_splitter

    @property
    def other_splitter(self):
        return self._other_splitter

    def check_circular(self, upstream):
        if upstream == self:
            return True
        if not isinstance(upstream,  AbstractDependentSplitter):
            return False
        return self.check_circular(upstream.other_splitter)

    @other_splitter.setter
    def other_splitter(self, new_value):
        """
        Supports the delayed setting ot the other to depend on

        :param new_value:
        :raise PacmanAlreadyExistsException:
            If there is already a different other set
        :raise PacmanPartitionException:
            If a circular depenceny is detected
        """
        if (self._other_splitter is not None and
                self._other_splitter != new_value):
            raise PacmanAlreadyExistsException(
                "other_splitter", self._other_splitter)
        if self.check_circular(new_value):
            raise PacmanPartitionException(
                "Ciruclar dependency found when setting splitter {} "
                "to be dependent on splitter {}".format(self, new_value))
        self._other_splitter = new_value
