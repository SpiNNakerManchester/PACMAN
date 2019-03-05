from collections import defaultdict, namedtuple, OrderedDict
import json
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine.router import Router
from pacman.utilities import file_format_schemas

# A description of a standard set of resources possessed by a chip
_Desc = namedtuple("_Desc", [
    # The cores where the monitors are
    "monitors",
    # The entries on the router
    "router_entries",
    # The speed of the router
    "router_clock_speed",
    # The amount of SDRAM on the chip
    "sdram",
    # Whether this is a virtual chip
    "virtual",
    # What tags this chip has
    "tags"])


class ConvertToJavaMachine(object):
    """ Converter from memory machine to java machine
    """

    __slots__ = []

    JAVA_MAX_INT = 2147483647

    def __call__(self, machine, file_path):
        """ Runs the code to write the machine in Java readable JSON.

        :param machine: Machine to convert
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param file_path: Location to write file to. Warning will overwrite!
        :type file_path: str
        """
        progress = ProgressBar(
            (machine.max_chip_x + 1) * (machine.max_chip_y + 1) + 2,
            "Converting to JSON machine")

        return ConvertToJavaMachine.do_convert(machine, file_path, progress)

    @staticmethod
    def int_value(value):
        if value < ConvertToJavaMachine.JAVA_MAX_INT:
            return value
        else:
            return ConvertToJavaMachine.JAVA_MAX_INT

    @staticmethod
    def _find_virtual_links(machine):
        """ Find all the virtual links and their inverse.

        As these may well go to an unexpected source

        :param machine: Machine to convert
        :return: Map of Chip to list of virtual links
        """
        virtual_links_dict = defaultdict(list)
        for chip in machine._virtual_chips:
            # assume all links need special treatment
            for link in chip.router.links:
                virtual_links_dict[chip].append(link)
                # Find and save inverse link as well
                inverse_id = (
                    (link.source_link_id + Router.MAX_LINKS_PER_ROUTER // 2)
                    % Router.MAX_LINKS_PER_ROUTER)
                destination = machine.get_chip_at(
                    link.destination_x, link.destination_y)
                inverse_link = destination.router.get_link(inverse_id)
                assert(inverse_link.destination_x == chip.x)
                assert(inverse_link.destination_y == chip.y)
                virtual_links_dict[destination].append(inverse_link)
        return virtual_links_dict

    @staticmethod
    def _describe_chip(chip, std, eth, virtual_links_dict):
        """ Produce a JSON-suitable description of a single chip.

        :param chip: The chip to describe.
        :param std: The standard chip resources.
        :param eth: The standard ethernet chip resources.
        :param virtual_links_dict: Where the virtual links are.
        :return: Description of chip that is trivial to serialize as JSON.
        """
        details = OrderedDict()
        details["cores"] = chip.n_processors
        if chip.nearest_ethernet_x is not None:
            details["ethernet"] =\
                [chip.nearest_ethernet_x, chip.nearest_ethernet_y]

        dead_links = []
        for link_id in range(0, Router.MAX_LINKS_PER_ROUTER):
            if not chip.router.is_link(link_id):
                dead_links.append(link_id)
        if dead_links:
            details["deadLinks"] = dead_links

        if chip in virtual_links_dict:
            links = []
            for link in virtual_links_dict[chip]:
                link_details = OrderedDict()
                link_details["sourceLinkId"] = link.source_link_id
                link_details["destinationX"] = link.destination_x
                link_details["destinationY"] = link.destination_y
                links.append(link_details)
            details["links"] = links

        exceptions = OrderedDict()
        router_entries = ConvertToJavaMachine.int_value(
            chip.router.n_available_multicast_entries)
        if chip.ip_address is not None:
            details['ipAddress'] = chip.ip_address
            # Write the Resources ONLY if different from the e_values
            if (chip.n_processors - chip.n_user_processors) != eth.monitors:
                exceptions["monitors"] = \
                    chip.n_processors - chip.n_user_processors
            if (router_entries != eth.router_entries):
                exceptions["routerEntries"] = router_entries
            if (chip.router.clock_speed != eth.router_clock_speed):
                exceptions["routerClockSpeed"] = \
                    chip.router.n_available_multicast_entries
            if chip.sdram.size != eth.sdram:
                exceptions["sdram"] = chip.sdram.size
            if chip.virtual != eth.virtual:
                exceptions["virtual"] = chip.virtual
            if chip.tag_ids != eth.tags:
                details["tags"] = list(chip.tag_ids)
        else:
            # Write the Resources ONLY if different from the s_values
            if (chip.n_processors - chip.n_user_processors) != std.monitors:
                exceptions["monitors"] = \
                    chip.n_processors - chip.n_user_processors
            if (router_entries != std.router_entries):
                exceptions["routerEntries"] = router_entries
            if (chip.router.clock_speed != std.router_clock_speed):
                exceptions["routerClockSpeed"] = \
                    chip.router.n_available_multicast_entries
            if chip.sdram.size != std.sdram:
                exceptions["sdram"] = chip.sdram.size
            if chip.virtual != std.virtual:
                exceptions["virtual"] = chip.virtual
            if chip.tag_ids != std.tags:
                details["tags"] = list(chip.tag_ids)

        if exceptions:
            return [chip.x, chip.y, details, exceptions]
        else:
            return [chip.x, chip.y, details]

    @staticmethod
    def do_convert(machine, file_path, progress=None):
        """ Runs the code to write the machine in Java readable JSON.

        :param machine: Machine to convert
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param file_path: Location to write file to. Warning will overwrite!
        :type file_path: str
        """

        # Find the std values for one non-ethernet chip to use as standard
        for chip in machine.chips:
            if chip.ip_address is None:
                std = _Desc(
                    monitors=chip.n_processors - chip.n_user_processors,
                    router_entries=ConvertToJavaMachine.int_value(
                        chip.router.n_available_multicast_entries),
                    router_clock_speed=chip.router.clock_speed,
                    sdram=chip.sdram.size,
                    virtual=chip.virtual,
                    tags=chip.tag_ids)
                break
        else:
            # Probably ought to warn if std is unpopulated
            pass

        # find the eth values to use for ethernet chips
        chip = machine.boot_chip
        eth = _Desc(
            monitors=chip.n_processors - chip.n_user_processors,
            router_entries=ConvertToJavaMachine.int_value(
                chip.router.n_available_multicast_entries),
            router_clock_speed=chip.router.clock_speed,
            sdram=chip.sdram.size,
            virtual=chip.virtual,
            tags=chip.tag_ids)

        # Save the standard data to be used as defaults to none ethernet chips
        standardResources = OrderedDict()
        standardResources["monitors"] = std.monitors
        standardResources["routerEntries"] = std.router_entries
        standardResources["routerClockSpeed"] = std.router_clock_speed
        standardResources["sdram"] = std.sdram
        standardResources["virtual"] = std.virtual
        standardResources["tags"] = list(std.tags)

        # Save the standard data to be used as defaults to none ethernet chips
        ethernetResources = OrderedDict()
        ethernetResources["monitors"] = eth.monitors
        ethernetResources["routerEntries"] = eth.router_entries
        ethernetResources["routerClockSpeed"] = eth.router_clock_speed
        ethernetResources["sdram"] = eth.sdram
        ethernetResources["virtual"] = eth.virtual
        ethernetResources["tags"] = list(eth.tags)

        # write basic stuff
        json_obj = OrderedDict()
        json_obj["height"] = machine.max_chip_y + 1
        json_obj["width"] = machine.max_chip_x + 1
        json_obj["root"] = list((machine.boot_x, machine.boot_y))
        json_obj["standardResources"] = standardResources
        json_obj["ethernetResources"] = ethernetResources
        json_obj["chips"] = []

        virtual_links_dict = ConvertToJavaMachine._find_virtual_links(machine)

        # handle chips
        for chip in machine.chips:
            json_obj["chips"].append(ConvertToJavaMachine._describe_chip(
                chip, std, eth, virtual_links_dict))

        if progress:
            progress.update()

        # dump to json file
        with open(file_path, "w") as f:
            json.dump(json_obj, f)

        if progress:
            progress.update()

        # validate the schema
        file_format_schemas.validate(json_obj, "jmachine.json")

        # update and complete progress bar
        if progress:
            progress.end()

        return file_path
