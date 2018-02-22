from pacman.utilities import constants
from pacman.utilities import file_format_schemas
from spinn_utilities.progress_bar import ProgressBar

from collections import defaultdict

import json

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
        exceptions = defaultdict(dict)
        for x in range(0, machine.max_chip_x + 1):
            for y in progress.over(range(0, machine.max_chip_y + 1), False):
                self._add_exceptions(json_obj, machine, x, y, exceptions)
        json_obj["chip_resource_exceptions"] = [
            [x, y, exceptions[x, y]] for x, y in exceptions]
        progress.update()

        # dump to json file
        with open(file_path, "w") as f:
            json.dump(json_obj, f)

        progress.update()

        # validate the schema
        file_format_schemas.validate(json_obj, "machine.json")

        # update and complete progress bar
        progress.end()

        return file_path

    def _add_exceptions(self, json_obj, machine, x, y, exceptions):
        # Handle non-existing/virtual chips by marking them as dead
        chip = machine.get_chip_at(x, y)
        if chip is None or chip.virtual:
            json_obj['dead_chips'].append([x, y])
            return

        # write dead links
        for link_id in range(0, ROUTER_MAX_NUMBER_OF_LINKS):
            if not chip.router.is_link(link_id):
                json_obj['dead_links'].append(
                    [x, y, "{}".format(constants.EDGES(link_id).name.lower())])

        # locate number of monitor cores and determine
        num_monitors = self._locate_no_monitors(chip)
        max_working_core = self._locate_max_core_id(chip)
        num_homogeneous_cores = max_working_core - num_monitors
        if num_homogeneous_cores != CHIP_HOMOGENEOUS_CORES:
            exceptions[x, y]["cores"] = num_homogeneous_cores

        # search for Ethernet connected chips
        for chip in machine.ethernet_connected_chips:
            exceptions[chip.x, chip.y]["tags"] = len(chip.tag_ids)

    @staticmethod
    def _locate_max_core_id(chip):
        for np in range(CHIP_HOMOGENEOUS_CORES, 0, -1):
            if chip.is_processor_with_id(np - 1):
                break
        return np - 1

    @staticmethod
    def _locate_no_monitors(chip):
        # search for monitors in the list of processors
        return sum(
            chip.is_processor_with_id(p)
            and chip.get_processor_with_id(p).is_monitor
            for p in range(0, CHIP_HOMOGENEOUS_CORES - 1))
