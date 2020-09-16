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
from pacman.operations.partitioner_splitters.splitter_slice_legacy import (
    SplitterSliceLegacy)


class SplitterSelector(object):
    """ splitter object selector that allocates nothing but legacy
    splitter objects where required
    """

    def __call__(self, app_graph):
        """ basic selector which puts the legacy splitter object on
        everything without a splitter object

        :param ApplicationGraph app_graph: app graph
        :rtype: None
        """
        for app_vertex in app_graph:
            if app_vertex.splitter_object is None:
                app_vertex.splitter_object = SplitterSliceLegacy()

