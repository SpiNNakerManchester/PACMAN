from collections import defaultdict
import json
import os

import jsonschema

from pacman.utilities import constants
from pacman.utilities import file_format_schemas
from spinn_machine.utilities.progress_bar import ProgressBar

CHIP_HOMOGENIOUS_CORES = 18
CHIP_HOMOGENIOUS_SDRAM = 119275520
CHIP_HOMOGENIOUS_SRAM = 24320
CHIP_HOMOGENIOUS_TAGS = 0
ROUTER_MAX_NUMBER_OF_LINKS = 6
ROUTER_HOMOGENIOUS_ENTRIES = 1024


class ConvertToFileMachine(object):
    """ Converter from memory machine to file machine
    """

    def __call__(self, machine, file_path):
        """

        :param machine:
        :param file_path:
        :return:
        """
        progress_bar = ProgressBar(
            ((machine.max_chip_x + 1) * (machine.max_chip_y + 1)) + 2,
            "Converting to json machine")

        # write basic stuff
        json_dictory_rep = dict()
        json_dictory_rep['width'] = machine.max_chip_x + 1
        json_dictory_rep['height'] = machine.max_chip_y + 1
        json_dictory_rep['chip_resources'] = dict()
        json_dictory_rep['chip_resources']['cores'] = CHIP_HOMOGENIOUS_CORES
        json_dictory_rep['chip_resources']['sdram'] = CHIP_HOMOGENIOUS_SDRAM
        json_dictory_rep['chip_resources']['sram'] = CHIP_HOMOGENIOUS_SRAM
        json_dictory_rep['chip_resources']["router_entries"] = \
            ROUTER_HOMOGENIOUS_ENTRIES
        json_dictory_rep['chip_resources']['tags'] = CHIP_HOMOGENIOUS_TAGS

        # handle exceptions
        json_dictory_rep['dead_chips'] = list()
        json_dictory_rep['dead_links'] = list()
        chip_resource_exceptions = defaultdict()

        # write dead chips
        for x_coord in range(0, machine.max_chip_x + 1):
            for y_coord in range(0, machine.max_chip_y + 1):
                if (not machine.is_chip_at(x_coord, y_coord) or
                        machine.get_chip_at(x_coord, y_coord).virtual):
                    json_dictory_rep['dead_chips'].append([x_coord, y_coord])
                else:
                    # write dead links
                    for link_id in range(0, ROUTER_MAX_NUMBER_OF_LINKS):
                        router = machine.get_chip_at(x_coord, y_coord).router
                        if not router.is_link(link_id):
                            json_dictory_rep['dead_links'].append(
                                [x_coord, y_coord, "{}".format(
                                 constants.EDGES(link_id).name.lower())])
                    self._check_for_exceptions(
                        json_dictory_rep, x_coord, y_coord, machine,
                        chip_resource_exceptions)
                progress_bar.update()

        # convert dict into list
        chip_resouce_exceptions_list = []
        for (chip_x, chip_y) in chip_resource_exceptions:
            chip_resouce_exceptions_list.append(
                [chip_x, chip_y, chip_resource_exceptions[(chip_x, chip_y)]])
        progress_bar.update()

        # store exceptions into json form
        json_dictory_rep['chip_resource_exceptions'] = \
            chip_resouce_exceptions_list

        # dump to json file
        file_to_write = open(file_path, "w")
        json.dump(json_dictory_rep, file_to_write)
        file_to_write.close()

        # validate the schema
        machine_schema_file_path = os.path.join(
            os.path.dirname(file_format_schemas.__file__), "machine.json"
        )
        file_to_read = open(machine_schema_file_path, "r")
        machine_schema = json.load(file_to_read)
        jsonschema.validate(
            json_dictory_rep, machine_schema)

        # update and complete progress bar
        progress_bar.update()
        progress_bar.end()

        return {'file_machine': file_path}

    def _check_for_exceptions(
            self, json_dictory_rep, x_coord, y_coord, machine,
            chip_resource_exceptions):
        """

        :param json_dictory_rep:
        :param x_coord:
        :param y_coord:
        :param machine:
        :return:
        """

        no_processors = CHIP_HOMOGENIOUS_CORES
        chip = machine.get_chip_at(x_coord, y_coord)

        if not chip.is_processor_with_id(no_processors - 1):

            # locate the highest core id
            has_processor = False
            while not has_processor and no_processors > 0:
                no_processors -= 1
                has_processor = machine.get_chip_at(x_coord, y_coord).\
                    is_processor_with_id(no_processors - 1)

            # locate number of monitor cores
            no_monitors = self._locate_no_monitors(chip)

            chip_exceptions = dict()
            chip_exceptions["cores"] = no_processors - no_monitors

            chip_resource_exceptions[(x_coord, y_coord)] = chip_exceptions

        else:
            no_monitors = self._locate_no_monitors(chip)

            # if monitors exist, remove them from top level
            if no_monitors > 0:
                chip_exceptions = dict()
                chip_exceptions["cores"] = \
                    CHIP_HOMOGENIOUS_CORES - 1 - no_monitors
                chip_resource_exceptions[(x_coord, y_coord)] = chip_exceptions

        # search for Ethernet connected chips
        for chip in machine.ethernet_connected_chips:
            if (chip.x, chip.y) not in chip_resource_exceptions:
                chip_resource_exceptions[(chip.x, chip.y)] = dict()
            chip_resource_exceptions[(chip.x, chip.y)]['tags'] = \
                len(chip.tag_ids)

    def _locate_no_monitors(self, chip):
        no_monitors = 0

        # search for monitors in the list of processors
        for processor in range(0, CHIP_HOMOGENIOUS_CORES - 1):
            if chip.is_processor_with_id(processor):
                if chip.get_processor_with_id(processor).is_monitor:
                    no_monitors += 1
        return no_monitors
