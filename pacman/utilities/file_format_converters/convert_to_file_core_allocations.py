from pacman.utilities import file_format_schemas
from pacman.utilities.utility_calls import ident

from spinn_utilities.progress_bar import ProgressBar

import json
from collections import OrderedDict


class ConvertToFileCoreAllocations(object):
    """ Converts placements to core allocations
    """

    __slots__ = []

    def __call__(self, placements, file_path):
        """
        :param placements:
        :param file_path:
        """

        progress = ProgressBar(len(placements) + 1,
                               "Converting to JSON core allocations")

        # write basic stuff
        json_obj = OrderedDict()
        json_obj['type'] = "cores"
        vertex_by_id = OrderedDict()

        # process placements
        for placement in progress.over(placements, False):
            self._convert_placement(placement, vertex_by_id, json_obj)

        # dump dict into json file
        with open(file_path, "w") as f:
            json.dump(json_obj, f)
        progress.update()

        # validate the schema
        file_format_schemas.validate(json_obj, "core_allocations.json")

        # complete progress bar
        progress.end()

        # return the file format
        return file_path, vertex_by_id

    def _convert_placement(self, placement, vertex_map, allocations_dict):
        vertex_id = ident(placement.vertex)
        vertex_map[vertex_id] = placement.vertex
        allocations_dict[vertex_id] = [placement.p, placement.p + 1]
