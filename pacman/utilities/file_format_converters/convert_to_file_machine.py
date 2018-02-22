from pacman.utilities import constants
from pacman.utilities import file_format_schemas
from spinn_utilities.progress_bar import ProgressBar

from collections import defaultdict

import json
import jsonschema
import os

CHIP_HOMOGENEOUS_CORES = 18
CHIP_HOMOGENEOUS_SDRAM = 119275520
CHIP_HOMOGENEOUS_SRAM = 24320
CHIP_HOMOGENEOUS_TAGS = 0
ROUTER_MAX_NUMBER_OF_LINKS = 6
ROUTER_HOMOGENEOUS_ENTRIES = 1024


class ConvertToFileMachine(object):
    """ Converter from memory machine to file machine
    """

    __slots__ = []

    def __call__(self, machine, file_path):
        """
        :param machine:
        :param file_path:
        """
        progress = ProgressBar(
            (machine.max_chip_x + 1) * (machine.max_chip_y + 1) + 2,
            "Converting to JSON machine")

        # write basic stuff
        json_obj = {
            "width": machine.max_chip_x + 1,
            "height": machine.max_chip_y + 1,
            "chip_resources": {
                "cores": CHIP_HOMOGENEOUS_CORES,
                "sdram": CHIP_HOMOGENEOUS_SDRAM,
                "sram": CHIP_HOMOGENEOUS_SRAM,
                "router_entries": ROUTER_HOMOGENEOUS_ENTRIES,
                "tags": CHIP_HOMOGENEOUS_TAGS},
            "dead_chips": [],
            "dead_links": []}

        # handle exceptions (dead chips)
        exceptions = defaultdict()
        for x in range(0, machine.max_chip_x + 1):
            for y in progress.over(range(0, machine.max_chip_y + 1), False):
                self._add_possibly_dead_chip(
                    json_obj, machine, x, y, exceptions)
        json_obj["chip_resource_exceptions"] = [
            [x, y, exceptions[x, y]] for x, y in exceptions]
        progress.update()

        # dump to json file
        with open(file_path, "w") as f:
            json.dump(json_obj, f)

        progress.update()

        # validate the schema
        schema_file = os.path.join(
            os.path.dirname(file_format_schemas.__file__), "machine.json")
        with open(schema_file, "r") as f:
            jsonschema.validate(json_obj, json.load(f))

        # update and complete progress bar
        progress.end()

        return file_path

    def _add_possibly_dead_chip(self, json_obj, machine, x, y, exceptions):
        if not machine.is_chip_at(x, y) or machine.get_chip_at(x, y).virtual:
            json_obj['dead_chips'].append([x, y])
            return

        # write dead links
        for link_id in range(0, ROUTER_MAX_NUMBER_OF_LINKS):
            router = machine.get_chip_at(x, y).router
            if not router.is_link(link_id):
                json_obj['dead_links'].append(
                    [x, y, "{}".format(constants.EDGES(link_id).name.lower())])

        chip = machine.get_chip_at(x, y)
        # locate number of monitor cores
        num_monitors = self._locate_no_monitors(chip)
        if not chip.is_processor_with_id(CHIP_HOMOGENEOUS_CORES - 1):
            # locate the highest core id
            num_processors = self._locate_max_core_id(machine, x, y)
            exceptions[x, y] = {
                "cores": num_processors - num_monitors}
        elif num_monitors:
            # if monitors exist, remove them from top level
            exceptions[x, y] = {
                "cores": CHIP_HOMOGENEOUS_CORES - 1 - num_monitors}

        # search for Ethernet connected chips
        for chip in machine.ethernet_connected_chips:
            if (chip.x, chip.y) not in exceptions:
                exceptions[chip.x, chip.y] = dict()
            exceptions[chip.x, chip.y]['tags'] = len(chip.tag_ids)

    @staticmethod
    def _locate_max_core_id(machine, x, y):
        for np in range(CHIP_HOMOGENEOUS_CORES, 0, -1):
            if machine.get_chip_at(x, y).is_processor_with_id(np - 1):
                break
        return np - 1

    @staticmethod
    def _locate_no_monitors(chip):
        # search for monitors in the list of processors
        return sum(
            p in chip and chip[p].is_monitor
            for p in range(0, CHIP_HOMOGENEOUS_CORES - 1))
