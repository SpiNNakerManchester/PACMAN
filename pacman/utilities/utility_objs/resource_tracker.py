# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections import defaultdict
from spinn_utilities.ordered_set import OrderedSet
from pacman.model.constraints.placer_constraints import (
    RadialPlacementFromChipConstraint, BoardConstraint, ChipAndCoreConstraint,
    AbstractPlacerConstraint)
from pacman.model.resources import (
    ConstantSDRAM, ResourceContainer, DTCMResource, CPUCyclesPerTickResource)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints, check_constrained_value,
    is_equal_or_None)
from pacman.exceptions import (
    PacmanCanNotFindChipException, PacmanInvalidParameterException,
    PacmanValueError, PacmanException)
from sortedcollections import ValueSortedDict
from pacman.utilities import constants


class ResourceTracker(object):
    """ Tracks the usage of resources of a machine.
    """

    __slots__ = [
        # The amount of SDRAM used by each chip,
        # indexed by the (x, y) tuple of coordinates of the chip
        # Note that entries are only added when the SDRAM is first used
        "_sdram_tracker",

        # The set of processor IDs available on each chip,
        # indexed by the (x, y) tuple of coordinates of the chip
        # Note that entries are only added when a core is first used
        "_core_tracker",

        # The machine object
        "_machine",

        # the number of timesteps that should be planned for
        "_plan_n_timesteps",

        # Set of tags available indexed by board address
        # Note that entries are only added when a board is first used
        "_tags_by_board",

        # Set of boards with available IP tags
        "_boards_with_ip_tags",

        # Set of (board_address, tag) assigned to an IP tag indexed by
        # (IP address, traffic identifier) - Note not reverse IP tags
        "_ip_tags_address_traffic",

        # The (IP address, traffic identifier) assigned to an IP tag indexed by
        # (board address, tag)
        "_address_and_traffic_ip_tag",

        # The (strip_sdp, port) assigned to an IP tag indexed by
        # (board address, tag)
        "_ip_tags_strip_sdp_and_port",

        # The (board address, port) combinations already assigned to a
        # reverse IP tag - Note not IP tags
        "_reverse_ip_tag_listen_port",

        # The port assigned to a reverse IP tag, indexed by
        # (board address, tag) - Note not IP tags
        "_listen_port_reverse_ip_tag",

        # A count of how many allocations are sharing the same IP tag -
        # Note not reverse IP tags
        "_n_ip_tag_allocations",

        # (x, y) tuple of coordinates of Ethernet connected chip indexed by
        # board address
        "_ethernet_chips",

        # Set of (x, y) tuples of coordinates of chips which have available
        # processors
        "_chips_available",

        # Number of cores preallocated on each chip (by x, y coordinates)
        "_n_cores_preallocated",

        # counter of chips that have had processors allocated to them
        "_chips_used",

        # The number of chips with the n cores currently available
        "_real_chips_with_n_cores_available",

        # the number of virtual chips with the n cores currently available
        "_virtual_chips_with_n_cores_available"
    ]

    ALLOCATION_SDRAM_ERROR = (
        "Allocating of {} bytes of SDRAM on chip {}:{} has failed as there "
        "are only {} bytes of SDRAM available on the chip at this time. "
        "Please fix and try again")

    def __init__(self, machine, plan_n_timesteps, chips=None,
                 preallocated_resources=None):
        """
        :param ~spinn_machine.Machine machine:
            The machine to track the usage of
        :param int plan_n_timesteps: number of timesteps to plan for
        :param chips: If specified, this list of chips will be used instead
            of the list from the machine. Note that the order will be
            maintained, so this can be used either to reduce the set of chips
            used, or to re-order the chips. Note also that on deallocation,
            the order is no longer guaranteed.
        :type chips: iterable(tuple(int, int)) or None
        :param preallocated_resources:
        :type preallocated_resources: PreAllocatedResourceContainer or None
        """

        # The amount of SDRAM available on each chip,
        # indexed by the (x, y) tuple of coordinates of the chip
        # Items are sorted in reverse order so highest comes out first
        self._sdram_tracker = ValueSortedDict(lambda x: -x)
        for chip in machine.chips:
            self._sdram_tracker[chip.x, chip.y] = chip.sdram.size

        # The set of processor IDs available on each chip,
        # indexed by the (x, y) tuple of coordinates of the chip
        # Note that entries are only added when a core is first used
        self._core_tracker = dict()

        # The machine object
        self._machine = machine

        # The number of timesteps that should be planned for.
        self._plan_n_timesteps = plan_n_timesteps

        # tracker for chips used
        self._chips_used = set()

        # Set of tags available indexed by board address
        # Note that entries are only added when a board is first used
        self._tags_by_board = dict()

        # Set of boards with available IP tags
        self._boards_with_ip_tags = OrderedSet()

        # Set of (board_address, tag) assigned
        # to any IP tag, indexed by (IP address, traffic_identifier)
        # - Note not reverse IP tags
        self._ip_tags_address_traffic = defaultdict(set)

        # The (IP address, traffic identifier) assigned to an IP tag indexed by
        # (board address, tag)
        self._address_and_traffic_ip_tag = dict()

        # The (strip_sdp, port) assigned to an IP tag indexed by
        # (board address, tag)
        self._ip_tags_strip_sdp_and_port = dict()

        # The (board address, port) combinations already assigned to a
        # reverse IP tag - Note not IP tags
        self._reverse_ip_tag_listen_port = set()

        # The port assigned to a reverse IP tag, indexed by
        # (board address, tag) - Note not IP tags
        self._listen_port_reverse_ip_tag = dict()

        # A count of how many allocations are sharing the same IP tag -
        # Note not reverse IP tags
        self._n_ip_tag_allocations = dict()

        # (x, y) tuple of coordinates of Ethernet connected chip indexed by
        # board address
        self._ethernet_chips = dict()
        for chip in self._machine.ethernet_connected_chips:
            self._ethernet_chips[chip.ip_address] = (chip.x, chip.y)
            self._boards_with_ip_tags.add(chip.ip_address)

        # set of resources that have been pre allocated and therefore need to
        # be taken account of when allocating resources
        self._n_cores_preallocated = self._convert_preallocated_resources(
            preallocated_resources)

        # update tracker for n cores available per chip
        self._real_chips_with_n_cores_available = \
            [0] * (machine.max_cores_per_chip() + 1)
        self._virtual_chips_with_n_cores_available = \
            [0] * (constants.CORES_PER_VIRTUAL_CHIP + 1)

        for chip in machine.chips:
            pre_allocated = 0
            if (chip.x, chip.y) in self._n_cores_preallocated:
                pre_allocated = self._n_cores_preallocated[(chip.x, chip.y)]
            if chip.virtual:
                self._virtual_chips_with_n_cores_available[
                    chip.n_user_processors - pre_allocated] += 1
            else:
                self._real_chips_with_n_cores_available[
                    chip.n_user_processors - pre_allocated] += 1

        # Set of (x, y) tuples of coordinates of chips which have available
        # processors
        self._chips_available = OrderedSet()
        if chips is None:
            for x, y in machine.chip_coordinates:
                self._chips_available.add((x, y))
        else:
            for x, y in chips:
                self._chips_available.add((x, y))

    @property
    def plan_n_time_steps(self):
        return self._plan_n_timesteps

    def _convert_preallocated_resources(self, preallocated_resources):
        """ Allocates preallocated SDRAM and specific cores to the trackers.\
            Also builds an arbitrary core map for use throughout resource\
            tracker.

        :param PreAllocatedResourceContainer preallocated_resources:
            the preallocated resources from the tools
        :return: a mapping of chip to arbitrary core demands
        :rtype: dict(tuple(int, int), int)
        """

        # If there are no resources, return an empty dict which returns 0
        if preallocated_resources is None:
            return defaultdict(lambda: 0)

        # remove SDRAM by removing from available SDRAM
        for sdram_pre_allocated in preallocated_resources.specific_sdram_usage:
            chip = sdram_pre_allocated.chip
            sdram = sdram_pre_allocated.sdram_usage.get_total_sdram(
                self._plan_n_timesteps)
            self._sdram_tracker[chip.x, chip.y] -= sdram

        # remove specific cores from the tracker
        for specific_core in preallocated_resources.specific_core_resources:
            chip = specific_core.chip
            processor_ids = specific_core.cores
            if not (chip.x, chip.y) in self._core_tracker:
                self._fill_in_core_tracker_for_chip((chip.x, chip.y), chip)
            for processor_id in processor_ids:
                self._core_tracker[chip.x, chip.y].remove(processor_id)

        # create random_core_map
        chip_to_arbitrary_core_requirement = defaultdict(lambda: 0)
        for arbitrary_core in preallocated_resources.core_resources:
            chip = arbitrary_core.chip
            n_cores = arbitrary_core.n_cores
            if (chip.x, chip.y) in chip_to_arbitrary_core_requirement:
                chip_to_arbitrary_core_requirement[chip.x, chip.y] += n_cores
            else:
                chip_to_arbitrary_core_requirement[chip.x, chip.y] = n_cores

        # handle specific IP tags
        ordered_ip_tags = sorted(
            preallocated_resources.specific_iptag_resources,
            key=lambda iptag: iptag.tag is None)
        for ip_tag in ordered_ip_tags:
            self._setup_board_tags(ip_tag.board)
            tag = self._allocate_tag_id(ip_tag.tag, ip_tag.board)
            self._update_data_structures_for_iptag(
                ip_tag.board, tag, ip_tag.ip_address,
                ip_tag.traffic_identifier, ip_tag.strip_sdp, ip_tag.port)

        # handle specific reverse IP tags
        for rip_tag in preallocated_resources.specific_reverse_iptag_resources:
            self._setup_board_tags(rip_tag.board)
            tag = self._allocate_tag_id(rip_tag.tag, rip_tag.board)
            self._update_structures_for_reverse_ip_tag(
                rip_tag.board, tag, rip_tag.port)

        return chip_to_arbitrary_core_requirement

    @staticmethod
    def check_constraints(
            vertices, additional_placement_constraints=None):
        """ Check that the constraints on the given vertices are supported\
            by the resource tracker.

        :param list(AbstractVertex) vertices:
            The vertices to check the constraints of
        :param set(AbstractConstraint) additional_placement_constraints:
            Additional placement constraints supported by the algorithm doing\
            this check
        :raises PacmanInvalidParameterException:
            If the constraints cannot be satisfied.
        """

        # These placement constraints are supported by the resource tracker
        placement_constraints = {
            ChipAndCoreConstraint, BoardConstraint,
            RadialPlacementFromChipConstraint
        }
        if additional_placement_constraints is not None:
            placement_constraints.update(additional_placement_constraints)

        # Check the placement constraints
        check_algorithm_can_support_constraints(
            constrained_vertices=vertices,
            supported_constraints=placement_constraints,
            abstract_constraint_type=AbstractPlacerConstraint)

    @staticmethod
    def get_ip_tag_info(resources, constraints):
        """ Get the IP tag resource information

        :param ResourceContainer resources:
            The resources to get the values from
        :param list(AbstractConstraint) constraints: A list of constraints
        :return:
            A tuple of board address, iterable of IP tag resources and
            iterable of reverse IP tag resources
        :rtype: tuple(str, iterable(~IptagResource),
            iterable(~ReverseIPtagResource))
        """
        board_address = None
        ip_tags = resources.iptags
        reverse_ip_tags = resources.reverse_iptags

        for constraint in constraints:
            if isinstance(constraint, BoardConstraint):
                board_address = check_constrained_value(
                    constraint.board_address, board_address)
        return board_address, ip_tags, reverse_ip_tags

    @staticmethod
    def get_chip_and_core(constraints, chips=None):
        """ Get an assigned chip and core from a set of constraints

        :param iterable(AbstractConstraint) constraints:
            The set of constraints to get the values from.
            Note that any type of constraint can be in the list but only those
            relevant will be used
        :param chips: Optional list of tuples of (x, y) coordinates of chips,
            restricting the allowed chips
        :type chips: iterable(tuple(int, int)) or None
        :return: tuple of a chip x and y coordinates, and processor ID, any of
            which might be None
        :rtype: tuple(int or None, int or None, int or None)
        """
        x = None
        y = None
        p = None
        for constraint in constraints:
            if isinstance(constraint, ChipAndCoreConstraint):
                x = check_constrained_value(constraint.x, x)
                y = check_constrained_value(constraint.y, y)
                p = check_constrained_value(constraint.p, p)

        if chips is not None and x is not None and y is not None:
            if (x, y) not in chips:
                raise PacmanInvalidParameterException(
                    "x, y and chips",
                    "{}, {} and {}".format(x, y, chips),
                    "The constraint cannot be met with the given chips")
        return x, y, p

    def _chip_available(self, x, y):
        """
        :param int x:
        :param int y:
        :rtype: bool
        """
        if not self._machine.is_chip_at(x, y):
            return False
        if (x, y) in self._core_tracker:
            projected_id = len(self._core_tracker[x, y])
        else:
            projected_id = self._machine.get_chip_at(x, y).n_user_processors
        return projected_id > self._n_cores_preallocated[x, y]

    def _get_usable_chips(self, chips, board_address):
        """ Get all chips that are available on a board given the constraints

        :param chips: iterable of tuples of (x, y) coordinates of chips to
            look though for usable chips, or None to use all available chips
        :type chips: iterable(tuple(int, int))
        :param board_address: the board address to check for usable chips on
        :type board_address: str or None
        :return: iterable of tuples of (x, y) coordinates of usable chips
        :rtype: iterable(tuple(int, int))
        :raise PacmanInvalidParameterException:
            * If the board address is unknown
            * When either or both chip coordinates of any chip are none
            * When a non-existent chip is specified
            * When all the chips in the specified board have been used
        """
        eth_chip = None
        if board_address is not None:
            if board_address not in self._ethernet_chips:
                raise PacmanInvalidParameterException(
                    "board_address", str(board_address),
                    "Unrecognised board address")
            eth_chip = self._machine.get_chip_at(
                *self._ethernet_chips[board_address])

        if chips is not None:
            area_code = None
            if eth_chip is not None:
                area_code = set(self._machine.get_existing_xys_on_board(
                    eth_chip))
            chip_found = False
            for (x, y) in chips:
                if ((area_code is None or (x, y) in area_code) and
                        self._chip_available(x, y)):
                    chip_found = True
                    yield (x, y)
            if not chip_found:
                self._check_chip_not_used(chips)
                raise PacmanInvalidParameterException(
                    "chips and board_address",
                    "{} and {}".format(chips, board_address),
                    "No valid chips found on the specified board")
        elif board_address is not None:
            for (x, y) in self._machine.get_existing_xys_on_board(eth_chip):
                if self._chip_available(x, y):
                    yield (x, y)
        else:
            for (x, y) in self._chips_available:
                if self._chip_available(x, y):
                    yield (x, y)

    def _check_chip_not_used(self, chips):
        """
        Check to see if any of the candidates chip have already been used.
        If not this may indicate the Chip was not there. Possibly a dead chip.

        :param chips: iterable of tuples of (x, y) coordinates of chips to
            look though for usable chips, or None to use all available chips
        :type chips: iterable(tuple(int, int))
        :raises PacmanCanNotFindChipException:
        """
        for chip in chips:
            if chip in self._chips_used:
                # Not a case of all the Chips never existed
                return
        raise PacmanCanNotFindChipException(
            "None of the chips {} were ever in the chips list".format(chips))

    @property
    def chips_available(self):
        """ The chips currently available

        :rtype: iterable(tuple(int,int))
        """
        return self._chips_available

    def _is_sdram_available(self, chip, resources):
        """ Check if the SDRAM available on a given chip is enough for the\
            given resources.

        :param ~spinn_machine.Chip chip: The chip to check the resources of
        :param ResourceContainer resources:
            the resources containing the SDRAM required
        :return: True if there is enough SDRAM available, or False otherwise
        :rtype: bool
        """
        return (self._sdram_tracker[chip.x, chip.y] >=
                resources.sdram.get_total_sdram(self._plan_n_timesteps))

    def _sdram_available(self, chip):
        """ Return the amount of SDRAM available on a chip

        :param ~spinn_machine.Chip chip: The chip to check the resources of
        :return: the SDRAM available
        :rtype: int
        """
        return self._sdram_tracker[chip.x, chip.y]

    def sdram_avilable_on_chip(self, chip_x, chip_y):
        """ Get the available SDRAM on the chip at coordinates chip_x, chip_y

        :param int chip_x: x coord of the chip in question
        :param int chip_y: y coord of the chip in question
        :return: the SDRAM remaining
        :rtype: int
        """
        chip = self._machine.get_chip_at(chip_x, chip_y)
        return self._sdram_available(chip)

    def _best_core_available(self, chip):
        """ Locate the best core available on a chip

        :param ~spinn_machine.Chip chip: The chip to check the resources of
        :return: The processor ID selected as the best on this chip
        :rtype: int
        """

        # TODO: Check for the best core; currently assumes all are the same
        key = (chip.x, chip.y)
        if key not in self._core_tracker:
            for processor in chip.processors:
                if not processor.is_monitor:
                    return processor.processor_id
        return next(iter(self._core_tracker[key]))

    def _is_core_available(self, chip, key, processor_id):
        """ Check if there is a core available on a given chip given the\
            constraints

        :param ~spinn_machine.Chip chip: The chip to check the resources of
        :param key: The (x, y) coordinates of the chip
        :type key: tuple(int, int)
        :param processor_id: A constraining fixed processor ID
        :type processor_id: int or None
        :return: whether there is a core available given the constraints
        :rtype: bool
        """
        return self._n_cores_available(chip, key, processor_id) > 0

    def _n_cores_available(self, chip, key, processor_id):
        """ Get the number of cores available on the given chip given the\
            constraints

        :param ~spinn_machine.Chip chip: The chip to check the resources of
        :param key: The (x, y) coordinates of the chip
        :type key: tuple(int, int)
        :param processor_id: A constraining fixed processor ID
        :type processor_id: int or None
        :return: The number of cores that meet the given constraints
        :rtype: int
        """

        # If a specific processor has been requested, perform special checks
        if processor_id is not None:

            # If the chip has already had cores allocated...
            if key in self._core_tracker:

                # Check if there is enough space for preallocated cores,
                # and that the processor specified is available
                return int(
                    len(self._core_tracker[key]) -
                    self._n_cores_preallocated[key] > 0
                    and processor_id in self._core_tracker[key])

            # If here, the chip has no cores allocated, so check that there
            # are enough cores on the chip for preallocated cores
            elif chip.n_user_processors - self._n_cores_preallocated[key] > 0:

                # Check that the processor is not a monitor core
                processor = chip.get_processor_with_id(processor_id)
                return int(processor is not None and not processor.is_monitor)

            # If we get here, the core has been allocated
            return 0

        # Check how many cores are available
        # TODO: Check the resources can be met with the processor
        # Currently assumes all processors are equal
        if key in self._core_tracker:
            n_cores = len(self._core_tracker[key])
        else:
            n_cores = sum(not proc.is_monitor for proc in chip.processors)
        return n_cores - self._n_cores_preallocated[key]

    def _get_matching_ip_tag(
            self, chip, board_address, tag_id, ip_address, port, strip_sdp,
            traffic_identifier):
        """ Attempt to locate a matching tag for the given details

        :param chip: The chip which is the source of the data for the tag
        :type chip: ~spinn_machine.Chip or None
        :param board_address: the board address to locate the chip on
        :type board_address: str or None
        :param tag_id: the tag ID to locate
        :type tag_id: int or None
        :param str ip_address: The IP address of the tag
        :param port: The port of the tag or None if not assigned
        :type port: int or None
        :param bool strip_sdp: True if the tag is to strip SDP header
        :param str traffic_identifier:
            The identifier of the traffic to pass over this tag
        :return: A board address, tag ID, and port or None, None, None if none
        :rtype: tuple of (str, int, (int or None)) or (None, None, None)
        """

        # If there is no tag for the given IP address - traffic identifier
        # combination, return
        if ((ip_address, traffic_identifier) not in
                self._ip_tags_address_traffic):
            return None, None, None

        # If no board address is specified, try to allow use of the closest
        # board
        eth_chip = None
        if board_address is None and chip is not None:
            eth_chip = self._machine.get_chip_at(
                chip.nearest_ethernet_x, chip.nearest_ethernet_y)

        # Scan the existing allocated tags and see if any match the details
        found_board = None
        found_tag = None
        found_port = None
        existing_tags = self._ip_tags_address_traffic[
            ip_address, traffic_identifier]
        for (other_board_address, other_tag) in existing_tags:
            (other_strip_sdp, other_port) = self._ip_tags_strip_sdp_and_port[
                other_board_address, other_tag]
            if (is_equal_or_None(other_board_address, board_address) and
                    is_equal_or_None(other_tag, tag_id) and
                    other_strip_sdp == strip_sdp and
                    is_equal_or_None(other_port, port)):

                # If the existing tag is on the same board, return immediately
                if (eth_chip is not None and
                        other_board_address == eth_chip.ip_address):
                    return other_board_address, other_tag, other_port

                # Otherwise store the tag for possible later use
                found_board = other_board_address
                found_tag = other_tag
                found_port = other_port

        # If we got here, we didn't find an existing tag on the same board
        # so check if the tag *could* be assigned to the current board
        if self._is_tag_available_on_ethernet_chip(eth_chip, tag_id):

            # If the tag is available, allow it to be used
            return None, None, None

        # Otherwise, return any matching existing tag
        return found_board, found_tag, found_port

    def _is_tag_available(self, board_address, tag):
        """ Check if a tag is available given the constraints

        :param board_address: the board address to locate the chip on
        :type board_address: str or None
        :param tag: the tag ID to locate
        :type tag: int or None
        :return: True if the tag is available, False otherwise
        :rtype: bool
        """
        if board_address is None and tag is not None:
            for board_addr in self._boards_with_ip_tags:
                if (board_addr not in self._tags_by_board or
                        tag in self._tags_by_board[board_addr]):
                    return True
            return False
        elif board_address is not None and tag is None:
            return board_address in self._boards_with_ip_tags
        elif board_address is None and tag is None:
            return bool(self._boards_with_ip_tags)
        return board_address not in self._tags_by_board \
            or tag in self._tags_by_board[board_address]

    def _is_tag_available_on_ethernet_chip(self, ethernet_chip, tag_id):
        """
        :param ethernet_chip:
        :type ethernet_chip: ~spinn_machine.Chip or None
        :param tag_id:
        :type tag_id: int or None
        :rtype: bool
        """
        if ethernet_chip is None:
            return False

        # Having found the board address, it can only be used if a
        # tag is available
        addr = ethernet_chip.ip_address
        return (addr in self._boards_with_ip_tags and
                (tag_id is None or addr not in self._tags_by_board or
                 tag_id in self._tags_by_board[addr]))

    def _is_ip_tag_available(self, board_address, ip_tag):
        """ Check if an IP tag is available given the constraints

        :param board_address: the board address to locate the chip on
        :type board_address: str or None
        :param tag: the tag ID to locate
        :type tag: int or None
        :param str ip_address: the IP address of the tag to be assigned
        :param port: the port number of the tag to be assigned
        :type port: int or None
        :param bool strip_sdp:
            if the IP tag has to be able to strip the SDP header
        :param str traffic_identifier: The type of traffic for the tag
        :return: True if a matching IP tag is available, False otherwise
        :rtype: bool
        """

        # If equivalent traffic is being used by another IP tag, re-use it
        (b_address, _, _) = self._get_matching_ip_tag(
            None, board_address, ip_tag.tag, ip_tag.ip_address, ip_tag.port,
            ip_tag.strip_sdp, ip_tag.traffic_identifier)
        if b_address is not None:
            return True

        # Otherwise determine if another tag is available
        return self._is_tag_available(board_address, ip_tag.tag)

    def _are_ip_tags_available(self, board_address, ip_tags):
        """ Check if the set of tags are available using the given chip,\
            given the constraints

        :param board_address: the board to allocate IP tags on
        :type board_address: str or None
        :param ip_tags: The IP tag resource
        :type ip_tags: iterable(IptagResource) or None
        :return: True if the tags can be allocated, False otherwise
        :rtype: bool
        """
        # If there are no tags to assign, declare that they are available
        if ip_tags is None or not ip_tags:
            return True

        # Check if each of the tags is available
        return all(
            self._is_ip_tag_available(board_address, ip_tag)
            for ip_tag in ip_tags)

    def _is_reverse_ip_tag_available(self, board_address, tag, port):
        """ Check if the reverse IP tag is available given the constraints

        :param board_address: The board address to use
        :type board_address: str or None
        :param tag: The tag to be used
        :type tag: int or None
        :param port: The port that the tag will listen on on the board
        :type port: int or None
        :return: True if the tag is available, false otherwise
        :rtype: int
        """
        if board_address is not None:

            # If the board address is not None, and the port is already
            # assigned, the tag is not available
            if (port is not None and
                    (board_address, port) in self._reverse_ip_tag_listen_port):
                return False

            # If the port is available, return true if the tag is available
            return self._is_tag_available(board_address, tag)

        # If the board address is not None but the port is already used
        # everywhere that the tag is available, the tag is not available.
        # Note that if port is None, any tag just has to be available
        if port is None:
            return any(self._is_tag_available(addr, tag)
                       for addr in self._boards_with_ip_tags)
        return any(
            (addr, port) not in self._reverse_ip_tag_listen_port
            and self._is_tag_available(addr, tag)
            for addr in self._boards_with_ip_tags)

    def _are_reverse_ip_tags_available(
            self, board_address, reverse_ip_tags):
        """ Check if this chip can be used given the reverse IP tag resources

        :param board_address: the board to allocate IP tags on
        :type board_address: str or None
        :param reverse_ip_tags: The reverse IP tag resource to be met
        :type reverse_ip_tags: iterable(ReverseIptagResource) or None
        :return: True if the chip can be used, False otherwise
        :rtype: bool
        """
        # If there are no tags, declare they are available
        if reverse_ip_tags is None or not reverse_ip_tags:
            return True

        return all(
            self._is_reverse_ip_tag_available(board_address, rip.tag, rip.port)
            for rip in reverse_ip_tags)

    def _allocate_sdram(self, chip, resources):
        """ Allocates the SDRAM on the given chip

        :param tuple(int,int) key: The (x, y) coordinates of the chip
        :param ResourceContainer resources:
            the resources containing the SDRAM required
        """
        self._sdram_tracker[chip.x, chip.y] -= \
            resources.sdram.get_total_sdram(self._plan_n_timesteps)

    def allocate_sdram(self, chip_x, chip_y, sdram_value):
        """ Allocates SDRAM value directly to a chip

        :param int chip_x: machine chip x coord.
        :param int chip_y: machine chip y coord.
        :param int sdram_value: the number of bytes to allocate
        :raises PacmanException: when the SDRAM can't be allocated
        """
        if self._sdram_tracker[chip_x, chip_y] - sdram_value < 0:
            raise PacmanException(self.ALLOCATION_SDRAM_ERROR.format(
                sdram_value, chip_x, chip_y,
                self._sdram_tracker[chip_x, chip_y]))
        else:
            self._sdram_tracker[chip_x, chip_y] -= sdram_value

    def _allocate_core(self, chip, key, processor_id):
        """ Allocates a core on the given chip

        :param ~spinn_machine.Chip chip: The chip to allocate the resources of
        :param tuple(int,int) key: The (x, y) coordinates of the chip
        :param processor_id:
            The ID of the processor to allocate, or None to pick automatically
        :type processor_id: int or None
        :rtype: int
        """
        if key not in self._core_tracker:
            self._fill_in_core_tracker_for_chip(key, chip)
        if processor_id is not None:
            self._core_tracker[key].remove(processor_id)
        else:
            # TODO: Find a core that meets the resource requirements
            processor_id = self._core_tracker[key].pop()

        # update number tracker
        if chip.virtual:
            self._virtual_chips_with_n_cores_available[
                len(self._core_tracker[key])] -= 1
            self._virtual_chips_with_n_cores_available[
                len(self._core_tracker[key]) - 1] += 1
        else:
            self._real_chips_with_n_cores_available[
                len(self._core_tracker[key])] -= 1
            self._real_chips_with_n_cores_available[
                len(self._core_tracker[key]) - 1] += 1

        if len(self._core_tracker[key]) == self._n_cores_preallocated[key]:
            self._chips_available.remove(key)

        # update chip tracker
        self._chips_used.add(key)

        # return processor ID
        return processor_id

    def _fill_in_core_tracker_for_chip(self, key, chip):
        """
        :param tuple(int,int) key:
        :param ~spinn_machine.Chip chip:
        """
        self._core_tracker[key] = set()
        for processor in chip.processors:
            if not processor.is_monitor:
                self._core_tracker[key].add(processor.processor_id)

    def _allocate_tag(self, chip, board_address, tag_id):
        """ Allocate a tag given the constraints

        :param ~spinn_machine.Chip chip:
            The chip containing the source of data for this tag
        :param board_address: the board address to allocate to
        :type board_address: str or None
        :param tag_id: the tag ID to allocate on this board address
        :type tag_id: int or None
        :return: (board address, tag)
        :rtype: tuple(str, int)
        """

        # First try to find a tag on the board closest to the chip
        if board_address is None:
            eth_chip = self._machine.get_chip_at(
                chip.nearest_ethernet_x, chip.nearest_ethernet_y)

            # verify if the Ethernet chip has the available tag ID
            if self._is_tag_available_on_ethernet_chip(eth_chip, tag_id):
                board_address = eth_chip.ip_address

        if board_address is None and tag_id is not None:
            for b_address in self._boards_with_ip_tags:
                if (b_address not in self._tags_by_board or
                        tag_id in self._tags_by_board[b_address]):
                    board_address = b_address
                    break
        elif board_address is None and tag_id is None:
            board_address = next(iter(self._boards_with_ip_tags))

        self._setup_board_tags(board_address)
        tag_id = self._allocate_tag_id(tag_id, board_address)

        if not self._tags_by_board[board_address]:
            self._boards_with_ip_tags.remove(board_address)
        return board_address, tag_id

    def _setup_board_tags(self, board_address):
        """ Establish the state for a given Ethernet chip if needed.

        :param str board_address:
            the board address to find the Ethernet chip of
        :rtype: None
        """
        if board_address not in self._tags_by_board:
            e_chip_x, e_chip_y = self._ethernet_chips[board_address]
            e_chip = self._machine.get_chip_at(e_chip_x, e_chip_y)
            self._tags_by_board[board_address] = set(e_chip.tag_ids)

    def _allocate_tag_id(self, tag_id, board_address):
        """ Locates a tag ID for the IP tag

        :param tag_id: tag ID to get, or None
        :type tag_id: int or None
        :param str board_address: board address
        :return: tag ID allocated
        :rtype: int
        """
        if tag_id is None:
            return self._tags_by_board[board_address].pop()
        self._tags_by_board[board_address].remove(tag_id)
        return tag_id

    def _allocate_ip_tags(self, chip, board_address, ip_tags):
        """ Allocate the given set of IP tag resources

        :param ~spinn_machine.Chip chip: The chip to allocate the tags for
        :param board_address: The board address to allocate on
        :type board_address: str or None
        :param iterable(IptagResource) ip_tags:
            The IP tag resources to allocate
        :return: iterable of tuples of (board address, tag) assigned
        :rtype: iterable(tuple(str, int, int, int)) or None
        """
        if ip_tags is None or not ip_tags:
            return None

        allocations = list()
        for ip_tag in ip_tags:

            # Find a tag that matches the one required
            (b_address, a_tag, a_port) = self._get_matching_ip_tag(
                chip, board_address, ip_tag.tag, ip_tag.ip_address,
                ip_tag.port, ip_tag.strip_sdp, ip_tag.traffic_identifier)

            if b_address is not None:
                # Get the chip with the Ethernet
                (e_chip_x, e_chip_y) = self._ethernet_chips[b_address]

                # If there is already an allocation that matches the current
                # tag, return this as the allocated tag
                allocations.append((b_address, a_tag, e_chip_x, e_chip_y))

                # Add to the number of things allocated to the tag
                self._n_ip_tag_allocations[b_address, a_tag] += 1

                # If the port is None and the requested port is not None,
                # update the port number
                if a_port is None and ip_tag.port is not None:
                    self._ip_tags_strip_sdp_and_port[b_address, a_tag] =\
                        (ip_tag.strip_sdp, a_port)
            else:

                # Allocate an IP tag
                (board_address, tag) = self._allocate_tag(
                    chip, board_address, ip_tag.tag)
                self._update_data_structures_for_iptag(
                    board_address, tag, ip_tag.ip_address,
                    ip_tag.traffic_identifier, ip_tag.strip_sdp, ip_tag.port)

                # Get the chip with the Ethernet
                (e_chip_x, e_chip_y) = self._ethernet_chips[board_address]

                allocations.append((board_address, tag, e_chip_x, e_chip_y))
        return allocations

    def _update_data_structures_for_iptag(self, board_address, tag, ip_address,
                                          traffic_identifier, strip_sdp, port):
        """
        :param str board_address:
        :param int tag:
        :param str ip_address:
        :param str traffic_identifier:
        :param bool strip_sdp:
        :param int port:
        """
        tag_key = (board_address, tag)
        existing_tags = self._ip_tags_address_traffic[
            ip_address, traffic_identifier]
        existing_tags.add(tag_key)
        self._ip_tags_strip_sdp_and_port[tag_key] = (strip_sdp, port)
        self._address_and_traffic_ip_tag[tag_key] = \
            (ip_address, traffic_identifier)

        # Remember how many allocations are sharing this tag
        # in case an deallocation is requested
        self._n_ip_tag_allocations[tag_key] = 1

    def _allocate_reverse_ip_tags(self, chip, board_address, reverse_ip_tags):
        """ Allocate reverse IP tags with the given constraints

        :param ~spinn_machine.Chip chip: The chip to allocate the tags for
        :param board_address: the board address to allocate on
        :type board_address: str or None
        :param iterable(ReverseIptagResource) reverse_ip_tags:
            The reverse IP tag resources
        :return: iterable of tuples of (board address, tag) assigned
        :rtype: iterable(tuple(str, int))
        """
        if reverse_ip_tags is None or not reverse_ip_tags:
            return None

        allocations = list()
        for reverse_ip_tag in reverse_ip_tags:
            (board_address, tag) = self._allocate_tag(
                chip, board_address, reverse_ip_tag.tag)
            allocations.append((board_address, tag))
            self._update_structures_for_reverse_ip_tag(
                board_address, tag, reverse_ip_tag.port)
        return allocations

    def _update_structures_for_reverse_ip_tag(self, board_address, tag, port):
        """ Updates the structures for reverse IP tags

        :param str board_address: the board its going to be placed on
        :param int tag: the tag ID
        :param port: the port number
        :type port: int or None
        :rtype: None
        """
        if port is not None:
            self._reverse_ip_tag_listen_port.add((board_address, port))
            self._listen_port_reverse_ip_tag[board_address, tag] = port

    def allocate_constrained_resources(
            self, resources, constraints, chips=None, vertices=None):
        """ Attempts to use the given resources of the machine, constrained\
            by the given placement constraints.

        :param ResourceContainer resources: The resources to be allocated
        :param list(AbstractConstraint) constraints:
            The constraints to consider
        :param iterable(tuple(int,int)) chips:
            The optional list of (x, y) tuples of chip coordinates of chips
            that can be used. Note that any chips passed in previously will
            be ignored
        :param vertices: the vertices related to these resources.
        :return:
            The x and y coordinates of the used chip, the processor_id,
            and the IP tag and reverse IP tag allocation tuples
        :rtype: tuple(int, int, int, list(tuple(int, int, int, int)),
            list(tuple(int, int)))
        :raise PacmanValueError:
            If the constraints cannot be met given the\
            current allocation of resources
        """
        (x, y, p) = self.get_chip_and_core(constraints, chips)
        (board_address, ip_tags, reverse_ip_tags) = \
            self.get_ip_tag_info(resources, constraints)
        if x is not None and y is not None:
            chips = [(x, y)]

        return self.allocate_resources(
            resources, chips, p, board_address, ip_tags, reverse_ip_tags)

    def allocate_constrained_group_resources(
            self, resource_and_constraint_list, chips=None):
        """ Allocates a group of cores on the same chip for these resources

        :param resource_and_constraint_list:
            A list of tuples of (resources, list of constraints) to allocate
        :type resource_and_constraint_list:
            list(tuple(ResourceContainer,AbstractConstraint))
        :param iterable(tuple(int,int)) chips:
            A list of chips that can be used
        :return: list of The x and y coordinates of the used chip, the
            processor_id, and the IP tag and reverse IP tag allocation tuples
        :rtype: iterable(tuple(int, int, int, list(tuple(int, int, int, int)),
            list(tuple(int, int))))
        """
        x = None
        y = None
        board_address = None
        processor_ids = list()
        group_ip_tags = list()
        group_reverse_ip_tags = list()
        for (resources, constraints) in resource_and_constraint_list:
            this_board, this_ip_tags, this_reverse_ip_tags = \
                self.get_ip_tag_info(resources, constraints)
            this_x, this_y, this_p = self.get_chip_and_core(constraints, chips)

            if (self.__different(x, this_x) or self.__different(y, this_y) or
                    (this_p is not None and this_p in processor_ids) or
                    self.__different(board_address, this_board)):
                raise PacmanException("Cannot merge conflicting constraints")
            x = x if this_x is None else this_x
            y = y if this_y is None else this_y
            board_address = board_address if this_board is None else this_board

            processor_ids.append(this_p)
            group_ip_tags.append(this_ip_tags)
            group_reverse_ip_tags.append(this_reverse_ip_tags)

        chips = None
        if x is not None and y is not None:
            chips = [(x, y)]

        # try to allocate in one block
        group_resources = [item[0] for item in resource_and_constraint_list]

        return self.allocate_group_resources(
            group_resources, chips, processor_ids, board_address,
            group_ip_tags, group_reverse_ip_tags)

    @staticmethod
    def __different(a, b):
        """
        :rtype: bool
        """
        return a is not None and b is not None and a != b

    def allocate_group_resources(
            self, group_resources, chips=None, processor_ids=None,
            board_address=None, group_ip_tags=None,
            group_reverse_ip_tags=None):
        """ Attempts to use the given group of resources on a single chip of
            the machine. Can be given specific place to use the resources, or
            else it will allocate them on the first place that the resources
            of the group fit together.

        :param list(ResourceContainer) group_resources:
            The resources to be allocated
        :param iterable(tuple(int,int)) chips:
            An iterable of (x, y) tuples of chips that are to be used
        :param processor_ids: The specific processor to use on any chip for
            each resource of the group
        :type processor_ids: list(int or None)
        :param str board_address:
            the board address to allocate resources of a chip
        :param list(list(IPtagResource)) group_ip_tags:
            list of lists of IP tag resources
        :param list(list(ReverseIPtagResource)) group_reverse_ip_tags:
            list of lists of reverse IP tag resources
        :return: An iterable of tuples of the x and y coordinates of the used
            chip, the processor_id, and the IP tag and reverse IP tag
            allocation tuples
        :rtype: iterable(tuple(int, int, int, list(tuple(int, int, int, int)),
            list(tuple(int, int))))
        :raises PacmanValueError:
            If there aren't chips available that can take the allocation.
        """

        usable_chips = self._get_usable_chips(chips, board_address)

        total_sdram = 0
        for resources in group_resources:
            total_sdram += resources.sdram.get_total_sdram(
                self._plan_n_timesteps)

        # Make arrays to make the next bit work
        if not group_ip_tags:
            group_ip_tags = [None for _ in group_resources]
        if not group_reverse_ip_tags:
            group_reverse_ip_tags = [None for _ in group_resources]
        if not processor_ids:
            processor_ids = [None for _ in group_resources]

        # Find the first usable chip which fits all the group resources
        tried_chips = list()
        for key in usable_chips:
            (chip_x, chip_y) = key
            tried_chips.append(key)
            chip = self._machine.get_chip_at(chip_x, chip_y)

            # No point in continuing if the chip doesn't have space for
            # everything
            if (self._n_cores_available(chip, key, None) >=
                    len(group_resources) and
                    self._sdram_available(chip) >= total_sdram):

                # Check that the constraints of all the resources can be met
                is_available = True
                for resources, processor_id, ip_tags, reverse_ip_tags in zip(
                        group_resources, processor_ids, group_ip_tags,
                        group_reverse_ip_tags):
                    if (not self._is_core_available(
                            chip, key, processor_id) or
                            not self._are_ip_tags_available(
                                board_address, ip_tags) or
                            not self._are_reverse_ip_tags_available(
                                board_address, reverse_ip_tags)):
                        is_available = False
                        break

                # If everything is good, do the allocation
                if is_available:
                    results = list()
                    for resources, proc_id, ip_tags, reverse_ip_tags in zip(
                            group_resources, processor_ids, group_ip_tags,
                            group_reverse_ip_tags):
                        processor_id = self._allocate_core(chip, key, proc_id)
                        self._allocate_sdram(chip, resources)
                        ip_tags_allocated = self._allocate_ip_tags(
                            chip, board_address, ip_tags)
                        reverse_ip_tags_allocated = \
                            self._allocate_reverse_ip_tags(
                                chip, board_address, reverse_ip_tags)
                        results.append((
                            chip.x, chip.y, processor_id, ip_tags_allocated,
                            reverse_ip_tags_allocated))
                    return results

        # If no chip is available, raise an exception
        resources = self._available_resources(tried_chips)
        all_chips = self._get_usable_chips(None, None)
        all_resources = self._available_resources(all_chips)
        raise PacmanValueError(
            "No resources available to allocate the given group resources"
            " within the given constraints:\n"
            "    Request for {} cores on a single chip with SDRAM: {}\n"
            "    Resources available which meet constraints:\n"
            "        {}\n"
            "    All Resources:\n"
            "        {}".format(len(group_resources), total_sdram, resources,
                                all_resources))

    def allocate_resources(
            self, resources, chips=None, processor_id=None,
            board_address=None, ip_tags=None, reverse_ip_tags=None):
        """ Attempts to use the given resources of the machine.  Can be given
        specific place to use the resources, or else it will allocate them on
        the first place that the resources fit.

        :param ResourceContainer resources: The resources to be allocated
        :param vertices: list of vertices for these resources
        :param iterable(tuple(int,int)) chips:
            An iterable of (x, y) tuples of chips that are to be used
        :param int processor_id: The specific processor to use on any chip.
        :param str board_address:
            The board address to allocate resources of a chip
        :param iterable(IPtagResource) ip_tags: iterable of IP tag resources
        :param iterable(ReverseIPtagResource) reverse_ip_tags:
            iterable of reverse IP tag resources
        :return: The x and y coordinates of the used chip, the processor_id,
            and the IP tag and reverse IP tag allocation tuples
        :rtype: tuple(int, int, int, list(tuple(int, int, int, int)),
            list(tuple(int, int)))
        :raises PacmanValueError:
            If there isn't a chip available that can take the allocation.
        """
        # Find the first usable chip which fits the resources
        for (chip_x, chip_y) in self._get_usable_chips(chips, board_address):
            chip = self._machine.get_chip_at(chip_x, chip_y)
            key = (chip_x, chip_y)

            if (self._is_core_available(chip, key, processor_id) and
                    self._is_sdram_available(chip, resources) and
                    self._are_ip_tags_available(board_address, ip_tags) and
                    self._are_reverse_ip_tags_available(board_address,
                                                        reverse_ip_tags)):
                processor_id = self._allocate_core(chip, key, processor_id)
                self._allocate_sdram(chip, resources)
                ip_tags_allocated = self._allocate_ip_tags(
                    chip, board_address, ip_tags)
                reverse_ip_tags_allocated = self._allocate_reverse_ip_tags(
                    chip, board_address, reverse_ip_tags)
                return (chip.x, chip.y, processor_id, ip_tags_allocated,
                        reverse_ip_tags_allocated)

        # If no chip is available, raise an exception
        if chips is not None and processor_id is not None:
            if len(chips) == 1:
                (x, y) = chips[0]
                raise PacmanValueError(
                    "Core {}:{}:{} is not available.".format(
                        x, y, processor_id))
            else:
                raise PacmanValueError(
                    "Processor id {} is not available on any of the chips"
                    "".format(processor_id))
        tried_chips = self._get_usable_chips(chips, board_address)
        left_resources = self._available_resources(tried_chips)
        all_chips = self._get_usable_chips(None, None)
        all_resources = self._available_resources(all_chips)
        raise PacmanValueError(
            "No resources available to allocate the given resources"
            " within the given constraints:\n"
            "    Request for CPU: {}, DTCM: {}, "
            "SDRAM fixed: {} per_timestep: {}, IP TAGS: {}, {}\n"
            "    Planning to run for {} timesteps.\n"
            "    Resources available which meet constraints:\n"
            "      {}\n"
            "    All resources available:\n"
            "      {}\n"
            .format(
                resources.cpu_cycles.get_value(), resources.dtcm.get_value(),
                resources.sdram.fixed, resources.sdram.per_timestep,
                resources.iptags, resources.reverse_iptags,
                self._plan_n_timesteps, left_resources, all_resources))

    def _available_resources(self, usable_chips):
        """ Describe how much of the various resource types are available.

        :param iterable(tuple(int,int)) usable_chips:
            Coordinates of usable chips
        :return: dict of board address to board resources
        :rtype: dict
        """
        resources_for_chips = dict()
        for x, y in usable_chips:
            resources_for_chip = dict()
            resources_for_chip["coords"] = (x, y)
            chip = self._machine.get_chip_at(x, y)
            if (x, y) in self._core_tracker:
                resources_for_chip["n_cores"] = (
                    len(self._core_tracker[x, y]) -
                    self._n_cores_preallocated[x, y])
            else:
                resources_for_chip["n_cores"] = (
                    chip.n_user_processors -
                    self._n_cores_preallocated[x, y])
            sdram_available = self._sdram_available(chip)
            resources_for_chip["sdram"] = sdram_available
            resources_for_chips[x, y] = resources_for_chip
        resources = dict()
        for board_address in self._boards_with_ip_tags:
            eth_x, eth_y = self._ethernet_chips[board_address]
            board_resources = dict()
            if board_address in self._tags_by_board:
                board_resources["n_tags"] = (
                    len(self._tags_by_board[board_address]))
            else:
                board_resources["n_tags"] = (
                    len(self._machine.get_chip_at(eth_x, eth_y).tag_ids))
            chips = list()
            for xy in self._machine.get_existing_xys_by_ethernet(eth_x, eth_y):
                chip_resources = resources_for_chips.get(xy)
                if chip_resources is not None:
                    chips.append(chip_resources)
            if chips:
                board_resources["chips"] = chips
            resources[board_address] = board_resources

        return resources

    def get_maximum_cores_available_on_a_chip(self):
        """ Returns the number of available cores of a real chip with the
            maximum number of available cores

        :return: the max cores available on the best real chip
        :rtype: int
        """
        for n_cores_available, n_chips_with_n_cores in reversed(list(
                enumerate(self._real_chips_with_n_cores_available))):
            if n_chips_with_n_cores != 0:
                return n_cores_available

    def get_maximum_cores_available_on_a_virtual_chip(self):
        """ Returns the number of available cores of a virtual chip with the
            maximum number of available cores

        :return: the max cores available on the best real chip
        :rtype: int
        """
        for n_cores_available, n_chips_with_n_cores in reversed(list(
                enumerate(self._virtual_chips_with_n_cores_available))):
            if n_chips_with_n_cores != 0:
                return n_cores_available
        return 0

    def get_maximum_constrained_resources_available(
            self, resources, constraints):
        """ Get the maximum resources available given the constraints

        :param ResourceContainer resources: The resources of the item to check
        :param iterable(AbstractConstraint) constraints:
        :rtype: ResourceContainer
        """
        (board_address, ip_tags, reverse_ip_tags) = self.get_ip_tag_info(
            resources, constraints)

        if not self._are_ip_tags_available(board_address, ip_tags):
            return ResourceContainer()
        if not self._are_reverse_ip_tags_available(
                board_address, reverse_ip_tags):
            return ResourceContainer()

        area_code = None
        if board_address is not None:
            if board_address not in self._ethernet_chips:
                raise PacmanInvalidParameterException(
                    "board_address", str(board_address),
                    "Unrecognised board address")
            eth_chip = self._machine.get_chip_at(
                *self._ethernet_chips[board_address])
            area_code = set(self._machine.get_existing_xys_on_board(eth_chip))

        (x, y, p) = self.get_chip_and_core(constraints)
        if x is not None and y is not None:
            if not self._chip_available(x, y):
                return ResourceContainer()
            if area_code is not None and (x, y) not in area_code:
                return ResourceContainer()
            best_processor_id = p
            chip = self._machine.get_chip_at(x, y)
            key = (x, y)
            sdram_available = self._sdram_available(chip)
            if p is not None and not self._is_core_available(chip, key, p):
                return ResourceContainer()
            if p is None:
                best_processor_id = self._best_core_available(chip)
            processor = chip.get_processor_with_id(best_processor_id)
            max_dtcm_available = processor.dtcm_available
            max_cpu_available = processor.cpu_cycles_available
            return ResourceContainer(
                DTCMResource(max_dtcm_available),
                ConstantSDRAM(sdram_available),
                CPUCyclesPerTickResource(max_cpu_available))

        return self.get_maximum_resources_available(area_code)

    def get_maximum_resources_available(self, area_code=None):
        """ Get the maximum resources available

        :param area_code: A set of valid (x, y) coordinates to choose from
        :type area_code: iterable(tuple(int,int)) or None
        :return: a resource which shows max resources available
        :rtype: ResourceContainer
        """
        # Go through the chips in order of sdram
        for ((chip_x, chip_y), sdram_available) in self._sdram_tracker.items():
            if self._chip_available(chip_x, chip_y) and (
                    area_code is None or (chip_x, chip_y) in area_code):
                chip = self._machine.get_chip_at(chip_x, chip_y)
                best_processor_id = self._best_core_available(chip)
                processor = chip.get_processor_with_id(best_processor_id)
                max_dtcm_available = processor.dtcm_available
                max_cpu_available = processor.cpu_cycles_available
                return ResourceContainer(
                    DTCMResource(max_dtcm_available),
                    ConstantSDRAM(sdram_available),
                    CPUCyclesPerTickResource(max_cpu_available))

        # Send the maximums
        # If nothing is available, return nothing
        return ResourceContainer()

    def unallocate_resources(self, chip_x, chip_y, processor_id, resources,
                             ip_tags, reverse_ip_tags):
        """ Undo the allocation of resources

        :param int chip_x: the x coord of the chip allocated
        :param int chip_y: the y coord of the chip allocated
        :param int processor_id: the processor ID
        :param ResourceContainer resources: The resources to be unallocated
        :param ip_tags: the details of the IP tags allocated
        :type ip_tags: iterable(tuple(str, int)) or None
        :param reverse_ip_tags: the details of the reverse IP tags allocated
        :type reverse_ip_tags: iterable(tuple(str, int)) or None
        :rtype: None
        """

        self._chips_available.add((chip_x, chip_y))
        self._sdram_tracker[chip_x, chip_y] += \
            resources.sdram.get_total_sdram(self._plan_n_timesteps)

        # update number tracker
        if self._machine.get_chip_at(chip_x, chip_y).virtual:
            self._virtual_chips_with_n_cores_available[
                len(self._core_tracker[chip_x, chip_y])] -= 1
            self._virtual_chips_with_n_cores_available[
                len(self._core_tracker[chip_x, chip_y]) + 1] += 1
        else:
            self._real_chips_with_n_cores_available[
                len(self._core_tracker[chip_x, chip_y])] -= 1
            self._real_chips_with_n_cores_available[
                len(self._core_tracker[chip_x, chip_y]) + 1] += 1

        self._core_tracker[chip_x, chip_y].add(processor_id)

        # check if chip used needs updating
        if (len(self._core_tracker[chip_x, chip_y]) ==
                self._machine.get_chip_at(chip_x, chip_y).n_user_processors):
            self._chips_used.remove((chip_x, chip_y))

        # Deallocate the IP tags
        if ip_tags is not None:
            for (board_address, tag, _, _) in ip_tags:
                self._boards_with_ip_tags.add(board_address)
                tag_key = (board_address, tag)
                self._n_ip_tag_allocations[tag_key] -= 1
                if self._n_ip_tag_allocations[tag_key] == 0:
                    key = self._address_and_traffic_ip_tag[tag_key]
                    del self._address_and_traffic_ip_tag[tag_key]
                    self._ip_tags_address_traffic[key].remove(tag_key)
                    if not self._ip_tags_address_traffic[key]:
                        del self._ip_tags_address_traffic[key]
                    self._tags_by_board[board_address].add(tag)
                    del self._ip_tags_strip_sdp_and_port[tag_key]

        # Deallocate the reverse IP tags
        if reverse_ip_tags is not None:
            for (board_address, tag) in reverse_ip_tags:
                self._boards_with_ip_tags.add(board_address)
                self._tags_by_board[board_address].add(tag)
                port = self._listen_port_reverse_ip_tag.get(
                    (board_address, tag), None)
                if port is not None:
                    del self._listen_port_reverse_ip_tag[board_address, tag]
                    self._reverse_ip_tag_listen_port.remove(
                        (board_address, port))

    def is_chip_available(self, chip_x, chip_y):
        """ Check if a given chip is available

        :param int chip_x: the x coord of the chip
        :param int chip_y: the y coord of the chip
        :return: True if the chip is available, False otherwise
        :rtype: bool
        """
        return (chip_x, chip_y) in self._chips_available

    @property
    def keys(self):
        """ The chip coordinates assigned

        :rtype: set(tuple(int,int))
        """
        return self._chips_used

    @property
    def chips_used(self):
        """ The number of chips used in this allocation.

        :rtype: int
        """
        return len(self._chips_used)
