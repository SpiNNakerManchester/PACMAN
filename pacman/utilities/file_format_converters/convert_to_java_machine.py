import json
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine.json_machine import to_json
from pacman.utilities import file_format_schemas


class ConvertToJavaMachine(object):
    """ Converter from memory machine to java machine
    """

    def __call__(self, machine, file_path):
        """ Runs the code to write the machine in Java readable JSON.

        :param machine: Machine to convert
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param file_path: Location to write file to. Warning will overwrite!
        :type file_path: str
        """
        # Steps are tojson, validate and writefile
        progress = ProgressBar(3, "Converting to JSON machine")

        return ConvertToJavaMachine.do_convert(machine, file_path, progress)

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
