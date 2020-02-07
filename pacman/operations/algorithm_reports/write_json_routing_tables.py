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
import os
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities import file_format_schemas
from pacman.model.routing_tables.multicast_routing_tables import to_json

_ROUTING_FILENAME = "routing_tables.json"


class WriteJsonRoutingTables(object):
    """ Converter from MulticastRoutingTables to json
    """

    def __call__(self, router_tables, json_folder):
        """ Runs the code to write the machine in Java readable JSON.

        :param router_tables: Routing Tables to convert
        :type router_tables:
            :py:class:`pacman.model.routing_tables.MulticastRoutingTables`
       :param json_folder: the folder to which the json are being written
       :type json_folder: str
        """
        # Steps are tojson, validate and writefile
        progress = ProgressBar(3, "Converting to JSON RouterTables")

        return WriteJsonRoutingTables.do_convert(
            router_tables, json_folder, progress)

    @staticmethod
    def do_convert(router_table, json_folder, progress=None):
        """ Runs the code to write the machine in Java readable JSON.

        :param machine: Machine to convert
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param json_folder: the folder to which the json are being written
        :type json_folder: str
        """

        file_path = os.path.join(json_folder, _ROUTING_FILENAME)
        json_obj = to_json(router_table)

        if progress:
            progress.update()

        # validate the schema
        file_format_schemas.validate(json_obj, _ROUTING_FILENAME)

        # update and complete progress bar
        if progress:
            progress.update()

        # dump to json file
        with open(file_path, "w") as f:
            json.dump(json_obj, f)

        if progress:
            progress.end()

        return file_path
