from pacman.utilities import file_format_schemas

from spinn_machine.utilities.progress_bar import ProgressBar

import os
import json
import jsonschema


class ConvertToFilePlacement(object):
    """ Converts memory placements to file placements
    """

    def __call__(self, placements, file_path):
        """

        :param placements: the memory placements object
        :param file_path: the file path for the placements.json
        :return: file path for the placements.json
        """

        # write basic stuff
        json_placement_dictory_rep = dict()
        vertex_by_id = dict()

        progress_bar = ProgressBar(len(placements.placements) + 1,
                                   "converting to json placements")

        # process placements
        for placement in placements:
            vertex_id = id(placement.vertex)
            vertex_by_id[vertex_id] = placement.vertex
            json_placement_dictory_rep[vertex_id] = [placement.x, placement.y]
            progress_bar.update()

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

        jsonschema.validate(
            json_placement_dictory_rep, placements_schema)

        progress_bar.update()
        progress_bar.end()

        # return the file format
        return file_path, vertex_by_id
