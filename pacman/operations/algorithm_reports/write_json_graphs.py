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
from pacman.utilities.json_utils import graphs_to_json
from jsonschema.exceptions import ValidationError

GRAPH_FILENAME = "graphs.json"
logger = FormatAdapter(logging.getLogger(__name__))


class WriteJsonGraphs(object):
    """ Converter (:py:obj:`callable`) from :py:class:`MulticastRoutingTables`
        to JSON.

    :param ApplicationGraph graph:
    :param graph_mapper:  TODO NUKE ME!
    :param str json_folder:
        The folder to which the reports are being written
    :return: The name of the actual file that was written
    :rtype: str
    """

    def __call__(self, application_graph, machine_graph, graph_mapper,
                 json_folder):
        # Steps are tojson, validate and writefile
        progress = ProgressBar(3, "Converting to JSON Graph")

        return WriteJsonGraphs.write_json(application_graph, machine_graph,
                                          graph_mapper, json_folder, progress)

    @staticmethod
    def write_json(application_graph, machine_graph, graph_mapper,
                   json_folder, progress=None):
        """ Runs the code to write the machine graph in Java readable JSON.

        :param ApplicationGraph application_graph:
        :param MachineGraph machine_graph:
        :param graph_mapper:  TODO NUKE ME!
        :param str json_folder:
            The folder to which the json are being written

            ..warning::
                Will overwrite existing file in this folder!

        :param ~spinn_utilities.progress_bar.ProgressBar progress:
        :return: the name of the generated file
        :rtype: str
        """

        file_path = os.path.join(json_folder, GRAPH_FILENAME)
        json_obj = graphs_to_json(
            application_graph, machine_graph, graph_mapper)

        if progress:
            progress.update()

        # validate the schema
        try:
            file_format_schemas.validate(json_obj, GRAPH_FILENAME)
        except ValidationError as ex:
            logger.error("JSON validation exception: {}\n{}",
                         ex.message, ex.instance)

        # update and complete progress bar
        if progress:
            progress.update()

        # dump to json file
        with open(file_path, "w") as f:
            json.dump(json_obj, f)

        if progress:
            progress.end()

        return file_path
