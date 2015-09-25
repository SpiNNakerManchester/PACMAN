"""

"""

from pacman.utilities import file_format_schemas

import os
import json
import validictory

class ConvertToFilePlacement(object):
    """

    """

    def __call__(self, placements, folder_path):
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

        # generate file path
        file_path = os.path.join(folder_path, "placements.json")

        # dump dict into json file
        json.dump(json_placement_dictory_rep, file_path)

        # validate the schema
        placements_schema_file_path = os.path.join(
            file_format_schemas.__file__, "placements.json"
        )
        validictory.validate(
            json_placement_dictory_rep, placements_schema_file_path)

        # return the file format
        return {"FilePlacements": file_path}