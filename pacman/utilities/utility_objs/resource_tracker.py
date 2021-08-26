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
from spinn_machine import Processor, SDRAM
from pacman.model.constraints.placer_constraints import (
    RadialPlacementFromChipConstraint, BoardConstraint, ChipAndCoreConstraint,
    AbstractPlacerConstraint)
from pacman.model.resources import (
    CoreTracker, ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource,
    ResourceContainer)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints, check_constrained_value,
    is_equal_or_None)
from pacman.exceptions import (
    PacmanCanNotFindChipException, PacmanInvalidParameterException,
    PacmanValueError, PacmanException)
from sortedcollections import ValueSortedDict


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

        # Values received by the init
        # The machine object
        "_machine",
        # the number of timesteps that should be planned for
        "_plan_n_timesteps",
        # Resources to be removed from each chip
        "_preallocated_resources",

        # sdram to be removed from from each ethernet chip
        # calculated using _preallocated_resources and _plan_n_timestep
        "_sdram_ethernet",

        # sdram to be removed from from each none ethernet chip
        # calculated using _preallocated_resources and _plan_n_timestep
        "_sdram_all",

        # Set of tags available indexed by board address
        # Note that entries are only added when a board is first tracked
        "_tags_by_board",

        # Set of boards with available IP tags
        # Note that entries are only added when a board is first tracked
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

        # Ethernet connected chips indexed by board address
        # The ones that have been tracked
        "_tracked_ethernet_chips",
        # The ones that have not t=yet been tracked
        "_untracked_ethernet_chips",

        # Set of (x, y) tuples of coordinates of chips which have available
        # processors
        # Note that entries are only added when a board is first tracked
        "_chips_available",

        # counter of chips that have had processors allocated to them
        "_chips_used",

        # The number of chips with the n cores currently available
        # Note that entries are only added when a board is first tracked
        "_real_chips_with_n_cores_available",
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
        self._tracked_ethernet_chips = dict()
        self._untracked_ethernet_chips = dict()

        # set of resources that have been pre allocated and therefore need to
        # be taken account of when allocating resources
        self._preallocated_resources = preallocated_resources
        if preallocated_resources:
            self._sdram_ethernet = preallocated_resources.sdram_ethernet. \
                get_total_sdram(self._plan_n_timesteps)
            self._sdram_all = preallocated_resources.sdram_all.get_total_sdram(
                self._plan_n_timesteps)
        else:
            self._sdram_ethernet = 0
            self._sdram_all = 0

        # update tracker for n cores available per chip
        self._real_chips_with_n_cores_available = \
            [0] * (machine.max_cores_per_chip() + 1)

        # Set of (x, y) tuples of coordinates of chips which have available
        # processors
        self._chips_available = OrderedSet()
        if chips is None:
            for chip in self._machine.ethernet_connected_chips:
                self._untracked_ethernet_chips[chip.ip_address] = chip
        else:
            for x, y in chips:
                self._track_chip(x, y)

    @property
    def plan_n_time_steps(self):
        return self._plan_n_timesteps

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

    def _track_chip(self, x, y):
        """
        Adds (if needed) a chip to the various tracker objects

        For all chips _core_tracker, _sdram_tracker and _chips_available

        For ethernet chips also _tags_by_board, _boards_with_ip_tags as
        well as moving the chip from untracked to tracked_ethernet_chips

        :param int x:
        :param int y:
        """
        if (x, y) in self._core_tracker:
            return
        chip = self._machine.get_chip_at(x, y)
        if chip is None:
            raise PacmanInvalidParameterException(
                "x and y",
                "({x}, {y})",
                f"There is no Chip {x}:{y} in the machine")
        self._core_tracker[x, y] = CoreTracker(
            chip, self._preallocated_resources,
            self._real_chips_with_n_cores_available)
        self._sdram_tracker[x, y] = chip.sdram.size
        self._chips_available.add((x, y))
        board_address = chip.ip_address
        if board_address:
            self._tracked_ethernet_chips[board_address] = chip
            if board_address in self._untracked_ethernet_chips:
                self._untracked_ethernet_chips.pop(board_address)
            if not chip.virtual:
                self._sdram_tracker[x, y] -= self._sdram_ethernet
            self._tags_by_board[board_address] = set(chip.tag_ids)
            self._boards_with_ip_tags.add(board_address)
            if self._preallocated_resources:
                for ip_tag in self._preallocated_resources.iptag_resources:
                    tag = self._allocate_tag_id(
                        ip_tag.tag, chip.ip_address)
                    self._update_data_structures_for_iptag(
                        chip.ip_address, tag, ip_tag.ip_address,
                        ip_tag.traffic_identifier, ip_tag.strip_sdp,
                        ip_tag.port)
        else:
            if not chip.virtual:
                self._sdram_tracker[x, y] -= self._sdram_all

    def _get_core_tracker(self, x, y):
        """
        Gets the core tracker after making sure it exists

        :param int x:
        :param int y:
        :return: The core tracker with preallocated resource removed
        """
        if (x, y) not in self._core_tracker:
            self._track_chip(x, y)
        return self._core_tracker[(x, y)]

    def _track_board(self, board_address):
        """
        Adds (if needed) a board and all its chips to the tracked objects

        :param str board_address:
        :raise PacmanInvalidParameterException:
            * If the board address is unknown
        """
        if board_address not in self._tracked_ethernet_chips:
            try:
                eth_chip = self._untracked_ethernet_chips.pop(board_address)
            except KeyError:
                raise PacmanInvalidParameterException(
                    "board_address", str(board_address),
                    "Unrecognised board address")
            for (x, y) in self._machine.get_existing_xys_on_board(eth_chip):
                self._track_chip(x, y)
                # track_chip updates tracked_ethernet_chips

    def _get_ethernet_chip(self, board_address):
        """
        Gets the ethernet chip for the board and ensure it is tracked

        :param str board_address:
        :return: EthernetChip
        :raise PacmanInvalidParameterException:
            * If the board address is unknown
        """
        self._track_board(board_address)
        return self._tracked_ethernet_chips[board_address]

    def _get_usable_chips_on_baord(self, chips, board_address):
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
        eth_chip = self._get_ethernet_chip(board_address)

        if chips is None:
            for (x, y) in self._machine.get_existing_xys_on_board(eth_chip):
                if self._get_core_tracker(x, y).is_available:
                    yield (x, y)
        else:
            area_code = set(self._machine.get_existing_xys_on_board(eth_chip))
            chip_found = False
            for (x, y) in chips:
                if ((x, y) in area_code and
                        self._get_core_tracker(x, y).is_available):
                    chip_found = True
                    yield (x, y)
            if not chip_found:
                self._check_chip_not_used(chips)
                raise PacmanInvalidParameterException(
                    "chips and board_address",
                    "{} and {}".format(chips, board_address),
                    "No valid chips found on the specified board")

    def _get_usable_chips_any_board(self, chips):
        """ Get all chips that are available on a board given the constraints

        :param chips: iterable of tuples of (x, y) coordinates of chips to
            look though for usable chips, or None to use all available chips
        :type chips: iterable(tuple(int, int))
        :return: iterable of tuples of (x, y) coordinates of usable chips
        :rtype: iterable(tuple(int, int))
        :raise PacmanInvalidParameterException:
            * If the board address is unknown
            * When either or both chip coordinates of any chip are none
            * When a non-existent chip is specified
            * When all the chips in the specified board have been used
        """
        if chips is None:
            for (x, y) in self._chips_available:
                if self._get_core_tracker(x, y).is_available:
                    yield (x, y)
            for board_address in list(self._untracked_ethernet_chips):
                eth_chip = self._get_ethernet_chip(board_address)
                for (x, y) in self._machine.get_existing_xys_on_board(
                        eth_chip):
                    yield (x, y)
        else:
            chip_found = False
            for (x, y) in chips:
                if self._get_core_tracker(x, y).is_available:
                    chip_found = True
                    yield (x, y)
            if not chip_found:
                self._check_chip_not_used(chips)
                raise PacmanInvalidParameterException(
                    "chips",
                    f"{chips}".format(chips),
                    "No valid chips found")

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
        if board_address is not None:
            yield from self._get_usable_chips_on_baord(chips, board_address)
        else:
            yield from self._get_usable_chips_any_board(chips)

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
        if eth_chip and self._is_tag_available(eth_chip.ip_address, tag_id):

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
        if board_address is None:
            if self._untracked_ethernet_chips:
                return True
            if tag is None:
                return bool(self._boards_with_ip_tags)
            else:
                for board_addr in self._boards_with_ip_tags:
                    if (board_addr not in self._tags_by_board or
                            tag in self._tags_by_board[board_addr]):
                        return True
                return False
        else:
            if board_address in self._untracked_ethernet_chips:
                return True
            if tag is None:
                return board_address in self._boards_with_ip_tags
            else:
                tag in self._tags_by_board[board_address]

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
        if self._untracked_ethernet_chips:
            return True
        if port is None:
            for addr in self._boards_with_ip_tags:
                if self._is_tag_available(addr, tag):
                    return True
        else:
            for addr in self._boards_with_ip_tags:
                if (addr, port) not in self._reverse_ip_tag_listen_port and\
                        self._is_tag_available(addr, tag):
                    return True
        return False

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
            if self._is_tag_available(eth_chip.ip_address, tag_id):
                board_address = eth_chip.ip_address

        if board_address is None:
            if tag_id is not None:
                for b_address in self._boards_with_ip_tags:
                    if (b_address not in self._tags_by_board or
                            tag_id in self._tags_by_board[b_address]):
                        board_address = b_address
                        break
            else:
                if self._boards_with_ip_tags:
                    board_address = self._boards_with_ip_tags.peek()

        if board_address is None:
            for board_address in self._untracked_ethernet_chips:
                break

        tag_id = self._allocate_tag_id(tag_id, board_address)

        if not self._tags_by_board[board_address]:
            self._boards_with_ip_tags.remove(board_address)
        return board_address, tag_id

    def _allocate_tag_id(self, tag_id, board_address):
        """ Locates a tag ID for the IP tag

        :param tag_id: tag ID to get, or None
        :type tag_id: int or None
        :param str board_address: board address
        :return: tag ID allocated
        :rtype: int
        """
        self._track_board(board_address)
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
                e_chip = self._get_ethernet_chip(b_address)

                # If there is already an allocation that matches the current
                # tag, return this as the allocated tag
                allocations.append((b_address, a_tag, e_chip.x, e_chip.y))

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
                e_chip = self._get_ethernet_chip(board_address)

                allocations.append((board_address, tag, e_chip.x, e_chip.y))
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
        if chips:
            chips = list(chips)
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

        if x is not None and y is not None:
            chips = [(x, y)]

        # try to allocate in one block
        group_resources = [item[0] for item in resource_and_constraint_list]

        return self._allocate_group_resources(
            group_resources, chips, processor_ids, board_address,
            group_ip_tags, group_reverse_ip_tags)

    @staticmethod
    def __different(a, b):
        """
        :rtype: bool
        """
        return a is not None and b is not None and a != b

    def _allocate_group_resources(
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
            tracker = self._get_core_tracker(chip_x, chip_y)
            if (tracker.n_cores_available >= len(group_resources) and
                    self._sdram_tracker[(chip_x, chip_y)] >= total_sdram):

                # Check that the constraints of all the resources can be met
                is_available = True
                for resources, processor_id, ip_tags, reverse_ip_tags in zip(
                        group_resources, processor_ids, group_ip_tags,
                        group_reverse_ip_tags):
                    if (not tracker.is_core_available(processor_id) or
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
                        self._chips_used.add(key)
                        processor_id = tracker.allocate(proc_id)
                        self._sdram_tracker[key] -= \
                            resources.sdram.get_total_sdram(
                                self._plan_n_timesteps)
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
            tracker = self._get_core_tracker(chip_x, chip_y)
            sdram_available = self._sdram_tracker[chip_x, chip_y] >= \
                resources.sdram.get_total_sdram(self._plan_n_timesteps)

            if (tracker.is_core_available(processor_id) and
                    sdram_available and
                    self._are_ip_tags_available(board_address, ip_tags) and
                    self._are_reverse_ip_tags_available(board_address,
                                                        reverse_ip_tags)):
                self._chips_used.add(key)
                processor_id = tracker.allocate(processor_id)
                self._sdram_tracker[chip_x, chip_y] -= \
                    resources.sdram.get_total_sdram(self._plan_n_timesteps)
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
        tried_chips = list(self._get_usable_chips(chips, board_address))
        left_resources = self._available_resources(tried_chips)
        all_chips = list(self._get_usable_chips(None, None))
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
            tracker = self._get_core_tracker(x, y)
            resources_for_chip["n_cores"] = tracker.n_cores_available
            resources_for_chip["sdram"] = self._sdram_tracker[x, y]
            resources_for_chips[x, y] = resources_for_chip
        resources = dict()

        # make sure all boards are tracked
        for board_address in list(self._untracked_ethernet_chips):
            self._track_board(board_address)

        for board_address in self._boards_with_ip_tags:
            eth_chip = self._get_ethernet_chip(board_address)
            board_resources = dict()
            board_resources["n_tags"] = (len(
                self._tags_by_board[board_address]))
            chips = list()
            for xy in self._machine.get_existing_xys_on_board(eth_chip):
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
        if self._untracked_ethernet_chips:
            # assume at least one chip on the board will have the max
            return self._machine.max_cores_per_chip()
        for n_cores_available, n_chips_with_n_cores in reversed(list(
                enumerate(self._real_chips_with_n_cores_available))):
            if n_chips_with_n_cores != 0:
                return n_cores_available

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
            eth_chip = self._get_ethernet_chip(board_address)
            area_code = set(self._machine.get_existing_xys_on_board(eth_chip))

        (x, y, p) = self.get_chip_and_core(constraints)
        if x is not None and y is not None:
            tracker = self._get_core_tracker(x, y)
            if not tracker.is_available:
                return ResourceContainer()
            if area_code is not None and (x, y) not in area_code:
                return ResourceContainer()
            best_processor_id = p
            chip = self._machine.get_chip_at(x, y)
            sdram_available = self._sdram_tracker[(x, y)]
            if p is not None and not tracker.is_core_available(p):
                return ResourceContainer()
            if p is None:
                best_processor_id = tracker.available_core()
            processor = chip.get_processor_with_id(best_processor_id)
            max_dtcm_available = processor.dtcm_available
            max_cpu_available = processor.cpu_cycles_available
            return ResourceContainer(
                DTCMResource(max_dtcm_available),
                ConstantSDRAM(sdram_available),
                CPUCyclesPerTickResource(max_cpu_available))

        return self._get_maximum_resources_available(area_code)

    def _get_maximum_resources_available(self, area_code=None):
        """ Get the maximum resources available

        :param area_code: A set of valid (x, y) coordinates to choose from
        :type area_code: iterable(tuple(int,int)) or None
        :return: a resource which shows max resources available
        :rtype: ResourceContainer
        """
        if self._untracked_ethernet_chips:
            # Assume at least one chip will have the maximum
            return ResourceContainer(
                DTCMResource(Processor.DTCM_AVAILABLE),
                ConstantSDRAM(SDRAM.DEFAULT_SDRAM_BYTES),
                CPUCyclesPerTickResource(Processor.CLOCK_SPEED // 1000))

        # Go through the chips in order of sdram
        for ((chip_x, chip_y), sdram_available) in self._sdram_tracker.items():
            tracker = self._get_core_tracker(chip_x, chip_y)
            if tracker.is_available and (
                    area_code is None or (chip_x, chip_y) in area_code):
                chip = self._machine.get_chip_at(chip_x, chip_y)
                best_processor_id = tracker.available_core()
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

        tracker = self._get_core_tracker(chip_x, chip_y)
        tracker.deallocate(processor_id)

        # check if chip used needs updating
        # if (len(self._core_tracker[chip_x, chip_y]) ==
        #        self._machine.get_chip_at(chip_x, chip_y).n_user_processors):
        #    self._chips_used.remove((chip_x, chip_y))

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
        return self._get_core_tracker(chip_x, chip_y).is_available

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
