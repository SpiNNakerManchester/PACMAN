import json
import os
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine.json_machine import to_json
from pacman.utilities import file_format_schemas
from pacman.model.routing_tables.multicast_routing_tables import to_json

_ROUTING_FILENAME = "routing_tables.json"


class ConvertToJsonRoutingTables(object):
    """ Converter from MulticastRoutingTables to json
    """

    def __call__(self, router_tables, report_folder):
        """ Runs the code to write the machine in Java readable JSON.

        :param router_tables: Routing Tables to convert
        :type router_tables:
            :py:class:`pacman.model.routing_tables.MulticastRoutingTables`
       :param report_folder: the folder to which the reports are being written
       :type report_folder: str
        """
        # Steps are tojson, validate and writefile
        progress = ProgressBar(2, "Converting to JSON RouterTables")

        file_path = os.path.join(report_folder, _ROUTING_FILENAME)
        return ConvertToJsonRoutingTables.do_convert(
            router_tables, file_path, progress)

    @staticmethod
    def do_convert(router_table, file_path, progress=None):
        """ Runs the code to write the machine in Java readable JSON.

        :param machine: Machine to convert
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param file_path: Location to write file to. Warning will overwrite!
        :type file_path: str
        """

        json_obj = to_json(router_table)

        if progress:
            progress.update()

        # validate the schema
        #file_format_schemas.validate(json_obj, "jmachine.json")

        # update and complete progress bar
        #if progress:
        #    progress.end()

        # dump to json file
        with open(file_path, "w") as f:
            json.dump(json_obj, f)

        if progress:
            progress.update()

        return file_path
