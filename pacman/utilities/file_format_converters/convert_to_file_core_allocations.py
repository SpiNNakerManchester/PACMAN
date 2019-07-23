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

import json
try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities import file_format_schemas
from pacman.utilities.utility_calls import ident


class ConvertToFileCoreAllocations(object):
    """ Converts placements to core allocations
    """

    __slots__ = []

    def __call__(self, placements, file_path):
        """
        :param placements:
        :param file_path:
        """

        progress = ProgressBar(len(placements) + 1,
                               "Converting to JSON core allocations")

        # write basic stuff
        json_obj = OrderedDict()
        json_obj['type'] = "cores"
        vertex_by_id = OrderedDict()

        # process placements
        for placement in progress.over(placements, False):
            self._convert_placement(placement, vertex_by_id, json_obj)

        # dump dict into json file
        with open(file_path, "w") as f:
            json.dump(json_obj, f)
        progress.update()

        # validate the schema
        file_format_schemas.validate(json_obj, "core_allocations.json")

        # complete progress bar
        progress.end()

        # return the file format
        return file_path, vertex_by_id

    def _convert_placement(self, placement, vertex_map, allocations_dict):
        vertex_id = ident(placement.vertex)
        vertex_map[vertex_id] = placement.vertex
        allocations_dict[vertex_id] = [placement.p, placement.p + 1]
