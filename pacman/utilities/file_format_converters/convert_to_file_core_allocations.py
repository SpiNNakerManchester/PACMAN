import os
import json

import jsonschema

from pacman.utilities import file_format_schemas
from spinn_machine.progress_bar import ProgressBar


class ConvertToFileCoreAllocations(object):
    """ Converts placements to core allocations
    """

    def __call__(self, placements, file_path):
        """

        :param placements:
        :param folder_path:
        :return:
        """

        progress_bar = ProgressBar(
            len(placements), "Converting to json core allocations")

        # write basic stuff
        json_core_allocations_dict = dict()

        json_core_allocations_dict['type'] = "cores"

        # process placements
        for placement in placements:
            json_core_allocations_dict[placement.subvertex.label] = \
                [placement.p, placement.p + 1]
            progress_bar.update()

        # dump dict into json file
        file_to_write = open(file_path, "w")
        json.dump(json_core_allocations_dict, file_to_write)
        file_to_write.close()

        # validate the schema
        core_allocations_schema_file_path = os.path.join(
            os.path.dirname(file_format_schemas.__file__),
            "core_allocations.json"
        )
        file_to_read = open(core_allocations_schema_file_path, "r")
        core_allocations_schema = json.load(file_to_read)
        jsonschema.validate(
            json_core_allocations_dict, core_allocations_schema)

        # complete progress bar
        progress_bar.end()

        # return the file format
        return {"FileCoreAllocations": file_path}
