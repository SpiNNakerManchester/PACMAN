from pacman.utilities import file_format_schemas

import os
import json
import validictory


class ConvertToFileCoreAllocations(object):
    """
    ConvertToFileCoreAllocations: converts placements to core allocations
    """

    def __call__(self, placements, folder_path):
        """

        :param placements:
        :param folder_path:
        :return:
        """

        # write basic stuff
        json_core_allocations_dict = dict()

        json_core_allocations_dict['type'] = "cores"

        # process placements
        for placement in placements:
            json_core_allocations_dict[placement.subvertex.label] = \
                [placement.p, placement.p + 1]

        # generate file path
        file_path = os.path.join(folder_path, "allocations_cores.json")

        # dump dict into json file
        json.dump(json_core_allocations_dict, file_path)

        # validate the schema
        core_allocations_schema_file_path = os.path.join(
            file_format_schemas.__file__, "core_allocations.json"
        )
        validictory.validate(
            json_core_allocations_dict, core_allocations_schema_file_path)

        # return the file format
        return {"FileCoreAllocations": file_path}
