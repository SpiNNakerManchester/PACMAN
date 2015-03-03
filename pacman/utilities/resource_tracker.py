from pacman.exceptions import PacmanValueError
from pacman.exceptions import PacmanInvalidParameterException
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.utilities.ordered_set import OrderedSet
from pacman.utilities import utility_calls
from pacman.model.resources.cpu_cycles_per_tick_resource \
    import CPUCyclesPerTickResource


class ResourceTracker(object):
    """ Tracks the usage of resources of a machine
    """

    def __init__(self, machine, chips=None):
        """

        :param machine: The machine to track the usage of
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param chips: If specified, this list of chips will be used\
            instead of the list from the machine.  Note that the order\
            will be maintained, so this can be used either to reduce the\
            set of chips used, or to re-order the chips.  Note also that\
            on de-allocation, the order is no longer guaranteed.
        :type chips: iterable of (x, y) tuples of coordinates of chips
        """

        # The amount of SDRAM used by each chip,
        # indexed by the (x, y) tuple of coordinates of the chip
        # Note that entries are only added when the SDRAM is first used
        self._sdram_tracker = dict()

        # The set of processor ids available on each chip,
        # indexed by the (x, y) tuple of coordinates of the chip
        # Note that entries are only added when a core is first used
        self._core_tracker = dict()

        # The machine object
        self._machine = machine

        # Set of tags available indexed by board address
        # Note that entries are only added when a board is first used
        self._tags_by_board = dict()

        # Set of boards with available ip tags
        self._boards_with_ip_tags = OrderedSet()

        # Set of (board_address, tag) assigned to an ip tag indexed by
        # (ip address, port, strip_sdp) - Note not reverse ip tags
        self._ip_tags_address_and_port = dict()

        # The (ip address, port) assigned to an ip tag indexed by
        # (board address, tag)
        self._address_and_port_ip_tag = dict()

        # The (board address, port) combinations already assigned to a
        # reverse ip tag - Note not ip tags
        self._reverse_ip_tag_listen_port = set()

        # The port assigned to a reverse ip tag, indexed by
        # (board address, tag) - Note not ip tags
        self._listen_port_reverse_ip_tag = dict()

        # A count of how many allocations are sharing the same ip tag -
        # Note not reverse ip tags
        self._n_ip_tag_allocations = dict()

        # Board address indexed by (x, y) tuple of coordinates of the chip
        self._ethernet_area_codes = dict()

        # (x, y) tuple of coordinates of ethernet connected chip indexed by
        # board address
        self._ethernet_chips = dict()

        # Set of (x, y) tuples of coordinates of chips which have available
        # processors
        self._chips_available = OrderedSet(chips)
        if chips is None:
            for chip in machine.chips:
                key = (chip.x, chip.y)
                self._chips_available.add(key)

        # Initialize the ethernet area codes
        for (chip_x, chip_y) in self._chips_available:
            chip = self._machine.get_chip_at(chip_x, chip_y)
            key = (chip_x, chip_y)

            # add area codes for ethernets
            ethernet_connected_chip = machine.get_chip_at(
                chip.nearest_ethernet_x, chip.nearest_ethernet_y)
            ethernet_area_code = ethernet_connected_chip.ip_address
            if ethernet_area_code not in self._ethernet_area_codes:
                self._ethernet_area_codes[ethernet_area_code] = OrderedSet()
                self._boards_with_ip_tags.add(ethernet_area_code)
                self._ethernet_chips[ethernet_area_code] = (
                    chip.nearest_ethernet_x, chip.nearest_ethernet_y)
            self._ethernet_area_codes[ethernet_area_code].add(key)

    def _get_usable_ip_tag_chips(self):
        for board_address in self._boards_with_ip_tags:
            for key in self._ethernet_area_codes[board_address]:
                if (key not in self._core_tracker
                        or len(self._core_tracker[key]) > 0):
                    yield key

    def _get_usable_chips(self, chips, board_address,
                          ip_tags, reverse_ip_tags):
        if chips is not None:
            chips_to_use = list()
            area_code = None
            if board_address is not None:
                if board_address not in self._ethernet_area_codes:
                    raise PacmanInvalidParameterException(
                        "board_address", board_address,
                        "Unrecognized board address")
                area_code = self._ethernet_area_codes[board_address]
            for (chip_x, chip_y) in chips:
                if ((chip_x is None and chip_y is not None)
                        or (chip_x is not None and chip_y is None)):
                    raise PacmanInvalidParameterException(
                        "chip_x and chip_y", "{} and {}".format(
                            chip_x, chip_y),
                        "Either both or neither must be None")
                if self._machine.get_chip_at(chip_x, chip_y) is None:
                    raise PacmanInvalidParameterException(
                        "chip_x and chip_y", "{} and {}".format(
                            chip_x, chip_y),
                        "No such chip was found in the machine")
                if ((chip_x, chip_y) in self._chips_available
                    and (area_code is None
                         or (chip_x, chip_y) in area_code)):
                    chips_to_use.append((chip_x, chip_y))
            if len(chips_to_use) == 0:
                raise PacmanInvalidParameterException(
                    "chips and board_address",
                    "{} and {}".format(chips, board_address),
                    "No valid chips found on the specified board")
            return chips_to_use
        elif board_address is not None:
            return self._ethernet_area_codes[board_address]
        elif ip_tags is not None or reverse_ip_tags is not None:
            return self._get_usable_ip_tag_chips()
        return self._chips_available

    def _is_sdram_available(self, chip, key, resources):
        if key in self._sdram_tracker:
            return ((chip.sdram.size - self._sdram_tracker[key])
                    > resources.sdram.get_value())
        else:
            return chip.sdram > resources.sdram.get_value()

    def _sdram_available(self, chip, key):
        if key not in self._sdram_tracker:
            return chip.sdram.size
        return chip.sdram.size - self._sdram_tracker[key]

    def _best_core_available(self, chip, key, processor_id):
        if processor_id is not None:
            return processor_id

        # TODO: Check for the best core; currently assumes all are the same
        if key not in self._core_tracker:
            for processor in chip.processors:
                if not processor.is_monitor:
                    return processor.processor_id
        return iter(self._core_tracker[key]).next()

    def _is_core_available(self, chip, key, processor_id, resources):

        # TODO: Check the resources can be met with the processor
        # Currently assumes all processors are equal and that resources
        # haven't been over allocated
        if processor_id is not None:
            if (key in self._core_tracker
                    and processor_id not in self._core_tracker[key]):
                return False
            elif key not in self._core_tracker:
                processor = chip.get_processor_with_id(processor_id)
                return processor is not None and not processor.is_monitor
        elif key in self._core_tracker:
            return len(self._core_tracker[key]) != 0

        return True

    def _get_matching_ip_tag(self, board_address, tag, key):
        if key not in self._ip_tags_address_and_port:
            return None, None
        existing_tags = self._ip_tags_address_and_port[key]
        if board_address is None and tag is not None:
            for (b_address, a_tag) in existing_tags:
                if a_tag == tag:
                    return (b_address, a_tag)
        elif board_address is not None and tag is None:
            for (b_address, a_tag) in existing_tags:
                if b_address == board_address:
                    return (b_address, a_tag)
        elif board_address is None and tag is None:
            return iter(existing_tags).next()
        elif (board_address, tag) in existing_tags:
            return (board_address, tag)
        return None, None

    def _is_tag_available(self, board_address, tag):
        if board_address is None and tag is not None:
            for board_address in self._boards_with_ip_tags:
                if (board_address not in self._tags_by_board
                        or tag in self._tags_by_board[board_address]):
                    return True
            return False
        elif board_address is not None and tag is None:
            return board_address in self._boards_with_ip_tags
        elif board_address is None and tag is None:
            return len(self._boards_with_ip_tags) > 0
        return (board_address not in self._tags_by_board
                or tag in self._tags_by_board[board_address])

    def _is_ip_tag_available(self, board_address, tag, ip_address, port,
                             strip_sdp):

        # If something is already sending to the same ip address and port but
        # is performing the opposite operation for strip sdp, then no tag can
        # be allocated
        reverse_strip_key = (ip_address, port, not strip_sdp)
        if reverse_strip_key in self._ip_tags_address_and_port:
            return False

        # If the same key is being used for another ip tag, re-use it
        key = (ip_address, port, strip_sdp)
        (b_address, _) = self._get_matching_ip_tag(board_address, tag, key)
        if b_address is not None:
            return True

        # Otherwise determine if another tag is available
        return self._is_tag_available(board_address, tag)

    def _are_ip_tags_available(self, chip, board_address, ip_tags):

        # If there are no tags to assign, declare that they are available
        if ip_tags is None:
            return True

        # If there is a fixed board address and the chip is not on the board
        # the tags are not available
        if (board_address is not None
                and (chip.x, chip.y)
                not in self._ethernet_area_codes[board_address]):
            return False

        # Check if each of the tags is available
        for ip_tag in ip_tags:
            if not self._is_ip_tag_available(board_address, ip_tag.tag,
                                             ip_tag.ip_address, ip_tag.port,
                                             ip_tag.strip_sdp):
                return False
        return True

    def _is_reverse_ip_tag_available(self, board_address, tag, port):

        if board_address is not None:

            # If the board address is not None, and the port is already
            # assigned, the tag is not available
            if (board_address, port) in self._reverse_ip_tag_listen_port:
                return False

            # If the port is available, return true if the tag is available
            return self._is_tag_available(board_address, tag)

        # If the board address is not None but the port is already used
        # everywhere that the tag is available, the tag is not available
        port_available = False
        for b_address in self._boards_with_ip_tags:
            if ((b_address, port) not in self._reverse_ip_tag_listen_port
                    and self._is_tag_available(b_address, tag)):
                port_available = True
                break
        return port_available

    def _are_reverse_ip_tags_available(self, chip, board_address,
                                       reverse_ip_tags):

        # If there are no tags, declare they are available
        if reverse_ip_tags is None:
            return True

        # If there is a fixed board address and the chip is not on the board
        # the tags are not available
        if (board_address is not None
                and not (chip.x, chip.y)
                in self._ethernet_area_codes[board_address]):
            return False

        for ip_tag in reverse_ip_tags:
            if not self._is_reverse_ip_tag_available(board_address,
                                                     ip_tag.tag, ip_tag.port):
                return False
        return True

    def _allocate_sdram(self, chip, key, resources):
        if key not in self._sdram_tracker:
            self._sdram_tracker[key] = resources.sdram.get_value()
        else:
            self._sdram_tracker[key] += resources.sdram.get_value()

    def _allocate_core(self, chip, key, processor_id, resources):
        if key not in self._core_tracker:
            self._core_tracker[key] = set()
            for processor in chip.processors:
                if not processor.is_monitor:
                    self._core_tracker[key].add(processor.processor_id)
        if processor_id is not None:
            self._core_tracker[key].remove(processor_id)
        else:

            # TODO: Find a core that meets the resource requirements
            processor_id = self._core_tracker[key].pop()

        if len(self._core_tracker[key]) == 0:
            self._chips_available.remove(key)
        return processor_id

    def _allocate_tag(self, board_address, tag):
        if board_address is None and tag is not None:
            for b_address in self._boards_with_ip_tags:
                if (b_address not in self._tags_by_board
                        or tag in self._tags_by_board[b_address]):
                    board_address = b_address
                    break
        elif board_address is None and tag is None:
            board_address = iter(self._boards_with_ip_tags).next()

        if board_address not in self._tags_by_board:
            (e_chip_x, e_chip_y) = self._ethernet_chips[board_address]
            e_chip = self._machine.get_chip_at(e_chip_x, e_chip_y)
            self._tags_by_board[board_address] = set(e_chip.tag_ids)

        if tag is None:
            tag = self._tags_by_board[board_address].pop()
        else:
            self._tags_by_board[board_address].remove(tag)

        if len(self._tags_by_board[board_address]) == 0:
            self._boards_with_ip_tags.remove(board_address)
        return (board_address, tag)

    def _allocate_ip_tags(self, board_address, ip_tags):
        if ip_tags is None:
            return None
        allocations = list()
        for ip_tag in ip_tags:
            key = (ip_tag.ip_address, ip_tag.port, ip_tag.strip_sdp)
            (b_address, a_tag) = self._get_matching_ip_tag(board_address,
                                                           ip_tag.tag, key)

            if b_address is not None:

                # If there is already an allocation that matches the current
                # tag, return this as the allocated tag
                allocations.append((b_address, a_tag))
            else:

                # Allocate an ip tag
                tag_key = self._allocate_tag(board_address, ip_tag.tag)

                # Remember that this tag is used for this ip address and port
                if key not in self._ip_tags_address_and_port:
                    self._ip_tags_address_and_port[key] = set()
                self._ip_tags_address_and_port[key].add(tag_key)
                self._address_and_port_ip_tag[tag_key] = key

                # Remember how many allocations are sharing this tag
                # in case an unallocation is requested
                if tag_key not in self._n_ip_tag_allocations:
                    self._n_ip_tag_allocations[tag_key] = 1
                else:
                    self._n_ip_tag_allocations[tag_key] += 1
                allocations.append(tag_key)
        if len(allocations) == 0:
            return None
        return allocations

    def _allocate_reverse_ip_tags(self, board_address, reverse_ip_tags):
        if reverse_ip_tags is None:
            return None
        allocations = list()
        for ip_tag in reverse_ip_tags:

            if board_address is not None:

                # If there is a board address, allocate the tag on the board
                (_, tag) = self._allocate_tag(board_address, ip_tag.tag)
                allocations.append((board_address, tag))
                self._reverse_ip_tag_listen_port.add(
                    (board_address, ip_tag.port))
                self._listen_port_reverse_ip_tag[
                    (board_address, ip_tag.tag)] = ip_tag.port

            else:

                # Otherwise, find the board with the port and tag available
                for b_address in self._boards_with_ip_tags:
                    if (((b_address, ip_tag.port)
                        not in self._reverse_ip_tag_listen_port)
                            and self._is_tag_available(board_address,
                                                       ip_tag.tag)):
                        (_, a_tag) = self._allocate_tag(board_address,
                                                        ip_tag.tag)
                        allocations.append((b_address, a_tag))
                        self._reverse_ip_tag_listen_port.add(
                            (b_address, ip_tag.port))
                        self._listen_port_reverse_ip_tag[
                            (board_address, ip_tag.tag)] = ip_tag.port
        if len(allocations) == 0:
            return None
        return allocations

    def allocate_constrained_resources(self, resources, constraints,
                                       chips=None):
        """ Attempts to use the given resources of the machine, constrained\
            by the given placement constraints.

        :param resources: The resources to be allocated
        :type resources:\
                    :py:class:`pacman.model.resources.resource_container.ResourceContainer`
        :param constraints: An iterable of constraints containing the\
                    :py:class:`pacman.model.constraints.placer_constraints.placer_chip_and_core_constraint.PlacerChipAndCoreConstraint`;\
                    note that other types are ignored and no exception will be\
                    thrown
        :type constraints: iterable of \
                    :py:class:`pacman.model.constraints.abstract_constraints.abstract_constraint.AbstractConstraint`
        :param chips: The optional list of (x, y) tuples of chip coordinates\
                    of chips that can be used.  Note that any chips passed in\
                    previously will be ignored
        :type chips: iterable of (int, int)
        :return: The x and y coordinates of the used chip, the processor_id,\
                 and the ip tag and reverse ip tag allocation tuples
        :rtype: (int, int, int, list((int, int)), list((int, int)))
        :raise PacmanValueError: If the constraints cannot be met given the\
                    current allocation of resources
        """
        (chips, p) = utility_calls.get_chip_and_core(constraints, chips)
        (board_address, ip_tags, reverse_ip_tags) = \
            utility_calls.get_ip_tag_info(constraints)

        return self.allocate_resources(resources, chips, p, board_address,
                                       ip_tags, reverse_ip_tags)

    def allocate_resources(self, resources, chips=None,
                           processor_id=None, board_address=None,
                           ip_tags=None, reverse_ip_tags=None):
        """ Attempts to use the given resources of the machine.  Can be given\
            specific place to use the resources, or else it will allocate them\
            on the first place that the resources fit.

        :param resources: The resources to be allocated
        :type resources:\
                    :py:class:`pacman.model.resources.resource_container.ResourceContainer`
        :param chips: An iterable of (x, y) tuples of chips that are to be used
        :param processor_id: The specific processor to use on any chip.
        :type processor_id: int
        :return: The x and y coordinates of the used chip, the processor_id,\
                 and the ip tag and reverse ip tag allocation tuples
        :rtype: (int, int, int, list((int, int)), list((int, int)))
        """
        usable_chips = self._get_usable_chips(chips, board_address,
                                              ip_tags, reverse_ip_tags)

        # Find the first usable chip which fits the resources
        for (chip_x, chip_y) in usable_chips:
            chip = self._machine.get_chip_at(chip_x, chip_y)
            key = (chip_x, chip_y)

            if (self._is_core_available(chip, key, processor_id, resources)
                    and self._is_sdram_available(chip, key, resources)
                    and self._are_ip_tags_available(
                        chip, board_address, ip_tags)
                    and self._are_reverse_ip_tags_available(
                        chip, board_address, reverse_ip_tags)):
                processor_id = self._allocate_core(
                    chip, key, processor_id, resources)
                self._allocate_sdram(chip, key, resources)
                ip_tags_allocated = self._allocate_ip_tags(
                    board_address, ip_tags)
                reverse_ip_tags_allocated = self._allocate_reverse_ip_tags(
                    board_address, reverse_ip_tags)
                return (chip.x, chip.y, processor_id, ip_tags_allocated,
                        reverse_ip_tags_allocated)

        # If no chip is available, raise an exception
        raise PacmanValueError(
            "No resources available to allocate the given resources"
            " within the given constraints")

    def get_maximum_constrained_resources_available(self, constraints,
                                                    chips=None):
        """ Get the maximum resources available given the constraints
        """
        (chips, p) = utility_calls.get_chip_and_core(constraints, chips)
        (board_address, ip_tags, reverse_ip_tags) = \
            utility_calls.get_ip_tag_info(constraints)
        return self.get_maximum_resources_available(chips, p, board_address,
                                                    ip_tags, reverse_ip_tags)

    def get_maximum_resources_available(self, chips=None, processor_id=None,
                                        board_address=None, ip_tags=None,
                                        reverse_ip_tags=None):
        """ Get the maximum resources available
        """
        usable_chips = self._get_usable_chips(chips, board_address,
                                              ip_tags, reverse_ip_tags)

        # If the chip is not fixed, find the maximum SDRAM
        # TODO: Also check for the best core
        max_sdram_available = 0
        max_dtcm_available = 0
        max_cpu_available = 0
        for (chip_x, chip_y) in usable_chips:
            key = (chip_x, chip_y)
            chip = self._machine.get_chip_at(chip_x, chip_y)
            sdram_available = self._sdram_available(chip, key)
            ip_tags_available = self._are_ip_tags_available(
                chip, board_address, ip_tags)
            reverse_ip_tags_available = self._are_reverse_ip_tags_available(
                chip, board_address, reverse_ip_tags)

            if (sdram_available > max_sdram_available
                    and ip_tags_available and reverse_ip_tags_available):
                max_sdram_available = sdram_available
                best_processor_id = self._best_core_available(chip, key,
                                                              processor_id)
                processor = chip.get_processor_with_id(best_processor_id)
                max_dtcm_available = processor.dtcm_available
                max_cpu_available = processor.cpu_cycles_available

            # If all the SDRAM on the chip is available,
            # this chip is unallocated, so the max must be the max
            # TODO: This assumes that the chips are all the same
            if sdram_available == chip.sdram.size:
                break

        # Send the maximums
        return ResourceContainer(
            DTCMResource(max_dtcm_available),
            SDRAMResource(max_sdram_available),
            CPUCyclesPerTickResource(max_cpu_available))

    def unallocate_resources(self, chip_x, chip_y, processor_id, resources,
                             ip_tags, reverse_ip_tags):
        """ Undo the allocation of resources
        """
        self._chips_available.add((chip_x, chip_y))
        self._sdram_tracker -= resources.sdram.get_value()
        self._core_tracker[(chip_x, chip_y)].add(processor_id)

        # Unallocate the ip tags
        if ip_tags is not None:
            for (board_address, tag) in ip_tags:
                self._boards_with_ip_tags.add(board_address)
                self._n_ip_tag_allocations[board_address] -= 1
                if self._n_ip_tag_allocations[board_address] == 0:
                    tag_key = (board_address, tag)
                    key = self._address_and_port_ip_tag[tag_key]
                    del self._address_and_port_ip_tag[tag_key]
                    self._ip_tags_address_and_port[key].remove(tag_key)
                    self._tags_by_board[board_address].add(tag)

        # Unallocate the reverse ip tags
        if reverse_ip_tags is not None:
            for (board_address, tag) in reverse_ip_tags:
                self._boards_with_ip_tags.add(board_address)
                self._tags_by_board[board_address].add(tag)
                port = self._listen_port_reverse_ip_tag[(board_address, tag)]
                del self._listen_port_reverse_ip_tag[(board_address, tag)]
                self._reverse_ip_tag_listen_port.remove((board_address, port))

    def is_chip_available(self, chip_x, chip_y):
        return (chip_x, chip_y) in self._chips_available

    @property
    def keys(self):
        return self._sdram_tracker.keys()
