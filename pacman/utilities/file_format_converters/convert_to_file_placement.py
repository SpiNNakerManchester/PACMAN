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
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities import file_format_schemas
from pacman.utilities.utility_calls import ident


class ConvertToFilePlacement(object):
    """ Converts memory placements to file placements
    """

    __slots__ = []

    def __call__(self, placements, file_path):
        """
        :param placements: the memory placements object
        :param file_path: the file path for the placements.json
        :return: file path for the placements.json
        """

        # write basic stuff
        json_obj = dict()
        vertex_by_id = dict()

        progress = ProgressBar(placements.n_placements + 1,
                               "converting to JSON placements")

        # process placements
        for placement in progress.over(placements, False):
            vertex_id = ident(placement.vertex)
            vertex_by_id[vertex_id] = placement.vertex
            json_obj[vertex_id] = [placement.x, placement.y]

        # dump dict into json file
        with open(file_path, "w") as file_to_write:
            json.dump(json_obj, file_to_write)
        progress.update()

        # validate the schema
        file_format_schemas.validate(json_obj, "placements.json")
        progress.end()

        # return the file format
        return file_path, vertex_by_id
