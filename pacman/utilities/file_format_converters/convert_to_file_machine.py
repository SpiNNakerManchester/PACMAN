from pacman.utilities import constants
from pacman.utilities import file_format_schemas

from collections import defaultdict

import json
#import validictory
import os

CHIP_HOMOGENIOUS_CORES = 18
CHIP_HOMOGENIOUS_SDRAM = 119275520
CHIP_HOMOGENIOUS_SRAM = 24320
CHIP_HOMOGENIOUS_TAGS = 0
ROUTER_MAX_NUMBER_OF_LINKS = 6
ROUTER_HOMOGENIOUS_ENTRIES = 1024


class ConvertToFileMachine(object):
    """
    converter from memory machien to file machine
    """

    def __call__(self, machine, file_path):
        """

        :param machine:
        :param file_path:
        :return:
        """

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

        # handel exceptions
        json_dictory_rep['dead_chips'] = list()
        json_dictory_rep['dead_links'] = list()
        chip_resource_exceptions = defaultdict()

        # write dead chips
        for x_coord in range(0, machine.max_chip_x + 1):
            for y_coord in range(0, machine.max_chip_y + 1):
                if (not machine.is_chip_at(x_coord, y_coord)
                        or machine.get_chip_at(x_coord, y_coord).virtual):
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

        # convert dict into list
        chip_resouce_exceptions_list = []
        for (chip_x, chip_y) in chip_resource_exceptions:
            chip_resouce_exceptions_list.append(
                [chip_x, chip_y, chip_resource_exceptions[(chip_x, chip_y)]])

        # store exceptions into json form
        json_dictory_rep['chip_resource_exceptions'] = \
            chip_resouce_exceptions_list

        # dump to json file
        machine_file_path = os.path.join(file_path, "machine.json")
        file_to_write = open(machine_file_path, "w")
        json.dump(json_dictory_rep, file_to_write)
        file_to_write.close()

        # validate the schema
        machine_schema_file_path = os.path.join(
            file_format_schemas.__file__, "machine.json"
        )

        #validictory.validate(
        #    json_dictory_rep, machine_schema_file_path)

        return {'file_machine': machine_file_path}

    @staticmethod
    def _check_for_exceptions(
            json_dictory_rep, x_coord, y_coord, machine,
            chip_resource_exceptions):
        """

        :param json_dictory_rep:
        :param x_coord:
        :param y_coord:
        :param machine:
        :return:
        """

        no_processors = CHIP_HOMOGENIOUS_CORES
        if (not machine.get_chip_at(x_coord, y_coord).
                is_processor_with_id(no_processors)):
            # locate the highest core id
            has_processor = False
            no_processors -= 1
            while not has_processor and no_processors > 0:
                has_processor = machine.get_chip_at(x_coord, y_coord).\
                    is_processor_with_id(no_processors)
                no_processors -= 1

            chip_exceptions = dict()
            chip_exceptions["cores"] = no_processors

            chip_resource_exceptions[(x_coord, y_coord)] = chip_exceptions

        for chip in machine.ethernet_connected_chips:
            chip_resource_exceptions[(chip.x, chip.y)]['tags'] = \
                len(chip.tag_ids)