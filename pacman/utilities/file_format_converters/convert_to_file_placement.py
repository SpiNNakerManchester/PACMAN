from pacman.utilities import file_format_schemas

from spinn_utilities.progress_bar import ProgressBar

import os
import json
import jsonschema


class ConvertToFilePlacement(object):
    """ Converts memory placements to file placements
    """

    __slots__ = []

    def __call__(self, placements, file_path):
        """

        :param placements: the memory placements object
        :param file_path: the file path for the placements.json
        :return: file path for the placements.json
        """

        # write basic stuff
        json_obj = dict()
        vertex_by_id = dict()

        progress = ProgressBar(placements.n_placements + 1,
                               "converting to json placements")

        # process placements
        for placement in progress.over(placements, False):
            vertex_id = str(id(placement.vertex))
            vertex_by_id[vertex_id] = placement.vertex
            json_obj[vertex_id] = [placement.x, placement.y]

        # dump dict into json file
        with open(file_path, "w") as file_to_write:
            json.dump(json_obj, file_to_write)

        # validate the schema
        placements_schema_file_path = os.path.join(
            os.path.dirname(file_format_schemas.__file__), "placements.json")

        progress.update()
        with open(placements_schema_file_path, "r") as file_to_read:
            jsonschema.validate(json_obj, json.load(file_to_read))
        progress.end()

        # return the file format
        return file_path, vertex_by_id
