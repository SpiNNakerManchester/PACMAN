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

import logging
import json
import os
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities import file_format_schemas
from pacman.utilities.json_utils import graph_to_json

_ROUTING_FILENAME = "machine_graph.json"
logger = FormatAdapter(logging.getLogger(__name__))


class ConvertToJsonMachineGraph(object):
    """ Converter from MulticastRoutingTables to json
    """

    def __call__(self, machine_graph, report_folder):
        """ Runs the code to write the machine in Java readable JSON.

        :param machine_graph: The machine_graph to place
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param report_folder: the folder to which the reports are being written
        :type report_folder: str
        """
        # Steps are tojson, validate and writefile
        progress = ProgressBar(3, "Converting to JSON MachineGraph")

        file_path = os.path.join(report_folder, _ROUTING_FILENAME)
        return ConvertToJsonMachineGraph.do_convert(
            machine_graph, file_path, progress)

    @staticmethod
    def do_convert(machine_graph, file_path, progress=None):
        """ Runs the code to write the machine in Java readable JSON.

        :param machine_graph: The machine_graph to place
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param file_path: Location to write file to. Warning will overwrite!
        :type file_path: str
        """

        json_obj = graph_to_json(machine_graph)

        if progress:
            progress.update()

        # validate the schema
        try:
            file_format_schemas.validate(json_obj, "machine_graph.json")
        except Exception as ex:
            logger.error("json valiation exception:\n {} \n {} \n".format(
                ex.message, ex.instance))

        # update and complete progress bar
        if progress:
            progress.update()

        # dump to json file
        with open(file_path, "w") as f:
            json.dump(json_obj, f)

        if progress:
            progress.end()

        return file_path
