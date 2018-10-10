from pacman.utilities import constants
from pacman.utilities import file_format_schemas
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine.router import Router

import json

CHIP_HOMOGENEOUS_CORES = 18


class ConvertToJavaMachine(object):
    """ Converter from memory machine to java machine
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

        for chip in machine.chips:
            monitors = chip.n_processors - chip.n_user_processors
            router_entries = chip.router.n_available_multicast_entries
            router_clock_speed = chip.router.clock_speed
            sdram = chip.sdram.size
            tags = len(chip.tag_ids)
            virtual = chip.virtual
            break

        # write basic stuff
        json_obj = {
            "width": machine.max_chip_x + 1,
            "height": machine.max_chip_y + 1,
            "chipResources": {
                "monitors": monitors,
                "routerEntries": router_entries,
                "routerClockSpeed": router_clock_speed,
                "sdram": sdram,
                "tags": tags,
                "virtual": virtual},
            "chips": [],
            "root": (machine.boot_x, machine.boot_y)
        }

        # handle chips
        for chip in machine.chips:
            details = dict()
            details["cores"] = chip.n_processors
            details["ethernet"] =\
                [chip.nearest_ethernet_x, chip.nearest_ethernet_x]
            dead_links = []
            for link_id in range(0, Router.MAX_LINKS_PER_ROUTER):
                if not chip.router.is_link(link_id):
                    dead_links.append(link_id)
            if len(dead_links) > 0:
                details["deadLinks"] = dead_links
            if chip.ip_address is not None:
                details['ipAddress'] = chip.ip_address

            exceptions = dict()
            if (chip.n_processors - chip.n_user_processors) != monitors:
                exceptions["monitors"] = chip.n_processors - chip.n_user_processors
            if (chip.router.n_available_multicast_entries != router_entries):
                exceptions["routerEntries"] = \
                    chip.router.n_available_multicast_entries
            if (chip.router.clock_speed != router_clock_speed):
                exceptions["routerClockSpeed"] = \
                    chip.router.n_available_multicast_entries
            if chip.sdram.size != sdram:
                exceptions["sdram"] = chip.sdram.size
            if len(chip.tag_ids) != tags:
                exceptions["tags"] = len(chip.tag_ids)
            if chip.virtual != virtual:
                exceptions["virtual"] = chip.virtual
            if len(exceptions) > 0:
                json_obj["chips"].append([chip.x, chip.y, details, exceptions])
            else:
                json_obj["chips"].append([chip.x, chip.y, details])

        progress.update()

        # dump to json file
        with open(file_path, "w") as f:
            json.dump(json_obj, f)

        progress.update()

        # validate the schema
        #file_format_schemas.validate(json_obj, "jmachine.json")

        # update and complete progress bar
        progress.end()

        return file_path
