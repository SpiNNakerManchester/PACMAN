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
from spinn_machine.json_machine import to_json
from pacman.utilities import file_format_schemas

MACHINE_FILENAME = "machine.json"


class ConvertToJsonMachine(object):
    """ Converter from memory machine to java machine
    """

    def __call__(self, machine, report_folder):
        """ Runs the code to write the machine in readable JSON.

        This is no longer the rig machine format

        :param machine: Machine to convert
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param report_folder: the folder to which the reports are being written
        :type report_folder: str
        """
        # Steps are tojson, validate and writefile
        progress = ProgressBar(3, "Converting to JSON machine")
        file_path = os.path.join(report_folder, MACHINE_FILENAME)

        return ConvertToJsonMachine.do_convert(machine, file_path, progress)

    @staticmethod
    def do_convert(machine, file_path, progress=None):
        """ Runs the code to write the machine in Java readable JSON.

        :param machine: Machine to convert
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param file_path: Location to write file to. Warning will overwrite!
        :type file_path: str
        """

        json_obj = to_json(machine)

        if progress:
            progress.update()

        # validate the schema
        file_format_schemas.validate(json_obj, "jmachine.json")

        # update and complete progress bar
        if progress:
            progress.end()

        # dump to json file
        with open(file_path, "w") as f:
            json.dump(json_obj, f)

        if progress:
            progress.update()

        return file_path
