"""

"""

from pacman.utilities import file_format_schemas

import os
import json
import validictory

class ConvertToFilePlacement(object):
    """

    """

    def __call__(self, placements, file_path):
        """

        :param placements:
        :param folder_path:
        :return:
        """
        # write basic stuff
        json_placement_dictory_rep = dict()

        # process placements
        for placement in placements:
            json_placement_dictory_rep[placement.subvertex.label] = \
                [placement.x, placement.y]

        # dump dict into json file
        file_to_write = open(file_path, "w")
        json.dump(json_placement_dictory_rep, file_to_write)
        file_to_write.close()

        # validate the schema
        placements_schema_file_path = os.path.join(
            os.path.dirname(file_format_schemas.__file__), "placements.json"
        )

        file_to_read = open(placements_schema_file_path, "r")
        placements_schema = json.load(file_to_read)

        validictory.validate(
            json_placement_dictory_rep, placements_schema)

        # return the file format
        return {"FilePlacements": file_path}