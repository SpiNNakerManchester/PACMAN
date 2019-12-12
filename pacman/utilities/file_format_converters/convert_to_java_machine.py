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
from spinn_machine.json_machine import to_json
from pacman.utilities import file_format_schemas


class ConvertToJavaMachine(object):
    """ Converter from memory machine to java machine

    :param ~spinn_machine.Machine machine: Machine to convert
    :param str file_path:
        Location to write file to.

        .. warn:
             This will be overwritten!
    """

    def __call__(self, machine, file_path):
        """ Runs the code to write the machine in Java readable JSON.

        :param ~spinn_machine.Machine machine:
        :param str file_path:
        """
        # Steps are tojson, validate and writefile
        progress = ProgressBar(3, "Converting to JSON machine")

        return ConvertToJavaMachine.do_convert(machine, file_path, progress)

    @staticmethod
    def do_convert(machine, file_path, progress=None):
        """ Runs the code to write the machine in Java readable JSON.

        :param ~spinn_machine.Machine machine: Machine to convert
        :param str file_path:
            Location to write file to.

            .. warn:
                 This will be overwritten!

        :param progress:
        :type progress: ~spinn_utilities.progress_bar.ProgressBar or None
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
