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
        :return:
        """
        progress_bar = ProgressBar(
            (machine.max_chip_x + 1) * (machine.max_chip_y + 1) + 2,
            "Converting to json machine")

        # write basic stuff
        json_obj = dict()
        json_obj['width'] = machine.max_chip_x + 1
        json_obj['height'] = machine.max_chip_y + 1
        json_obj['chip_resources'] = dict()
        json_obj['chip_resources']['cores'] = CHIP_HOMOGENEOUS_CORES
        json_obj['chip_resources']['sdram'] = CHIP_HOMOGENEOUS_SDRAM
        json_obj['chip_resources']['sram'] = CHIP_HOMOGENEOUS_SRAM
        json_obj['chip_resources']["router_entries"] = \
            ROUTER_HOMOGENEOUS_ENTRIES
        json_obj['chip_resources']['tags'] = CHIP_HOMOGENEOUS_TAGS

        # handle exceptions
        json_obj['dead_chips'] = list()
        json_obj['dead_links'] = list()
        chip_resource_exceptions = defaultdict()

        # write dead chips
        for x_coord in range(0, machine.max_chip_x + 1):
            for y_coord in range(0, machine.max_chip_y + 1):
                self._add_possibly_dead_chip(json_obj, machine,
                                             x_coord, y_coord,
                                             chip_resource_exceptions)
                progress_bar.update()

        # convert dict into list
        chip_resource_exceptions_list = []
        for (chip_x, chip_y) in chip_resource_exceptions:
            chip_resource_exceptions_list.append(
                [chip_x, chip_y, chip_resource_exceptions[(chip_x, chip_y)]])
        progress_bar.update()

        # store exceptions into json form
        json_obj['chip_resource_exceptions'] = chip_resource_exceptions_list

        # dump to json file
        with open(file_path, "w") as file_to_write:
            json.dump(json_obj, file_to_write)

        # validate the schema
        machine_schema_file_path = os.path.join(
            os.path.dirname(file_format_schemas.__file__), "machine.json")
        with open(machine_schema_file_path, "r") as file_to_read:
            jsonschema.validate(json_obj, json.load(file_to_read))

        # update and complete progress bar
        progress_bar.update()
        progress_bar.end()

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
        if not chip.is_processor_with_id(CHIP_HOMOGENEOUS_CORES - 1):
            # locate the highest core id
            no_processors = self._locate_core_id(machine, x, y)
            # locate number of monitor cores
            no_monitors = self._locate_no_monitors(chip)
            chip_exceptions = dict()
            chip_exceptions["cores"] = no_processors - no_monitors
            exceptions[(x, y)] = chip_exceptions

        else:
            no_monitors = self._locate_no_monitors(chip)

            # if monitors exist, remove them from top level
            if no_monitors > 0:
                chip_exceptions = dict()
                chip_exceptions["cores"] = \
                    CHIP_HOMOGENEOUS_CORES - 1 - no_monitors
                exceptions[(x, y)] = chip_exceptions

        # search for Ethernet connected chips
        for chip in machine.ethernet_connected_chips:
            if (chip.x, chip.y) not in exceptions:
                exceptions[(chip.x, chip.y)] = dict()
            exceptions[(chip.x, chip.y)]['tags'] = len(chip.tag_ids)

    @staticmethod
    def _locate_core_id(machine, x, y):
        no_processors = CHIP_HOMOGENEOUS_CORES
        has_processor = False
        while not has_processor and no_processors > 0:
            no_processors -= 1
            has_processor = machine.get_chip_at(x, y).\
                is_processor_with_id(no_processors - 1)
        return no_processors

    @staticmethod
    def _locate_no_monitors(chip):
        no_monitors = 0

        # search for monitors in the list of processors
        for processor in range(0, CHIP_HOMOGENEOUS_CORES - 1):
            if chip.is_processor_with_id(processor) and \
                    chip.get_processor_with_id(processor).is_monitor:
                no_monitors += 1
        return no_monitors
