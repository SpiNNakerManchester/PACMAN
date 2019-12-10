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


class ConvertToJsonRoutingTables(object):
    """ Converter (:py:obj:`callable`) from MulticastRoutingTables to JSON

    :param MulticastRoutingTables router_tables: Routing Tables to convert
    :param str report_folder:
        the folder to which the reports are being written
    """

    def __call__(self, router_tables, report_folder):
        """ Runs the code to write the machine in Java readable JSON.
        """
        # Steps are tojson, validate and writefile
        progress = ProgressBar(3, "Converting to JSON RouterTables")

        file_path = os.path.join(report_folder, _ROUTING_FILENAME)
        return ConvertToJsonRoutingTables.do_convert(
            router_tables, file_path, progress)

    @staticmethod
    def do_convert(router_table, file_path, progress=None):
        """ Runs the code to write the machine in Java readable JSON.

        :param ~spinn_machine.machine.Machine machine: Machine to convert
        :param str file_path:
            Location to write file to. Warning will overwrite!
        """

        json_obj = to_json(router_table)

        if progress:
            progress.update()

        # validate the schema
        file_format_schemas.validate(json_obj, "router.json")

        # update and complete progress bar
        if progress:
            progress.update()

        # dump to json file
        with open(file_path, "w") as f:
            json.dump(json_obj, f)

        if progress:
            progress.end()

        return file_path
