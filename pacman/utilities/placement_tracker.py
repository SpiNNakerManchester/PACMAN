from pacman import exceptions


class PlacementTracker():
    """ placement tracker object for usage in placement algoirthms

    """

    def __init__(self, machine):
        self._placements_available = dict()
        self._ethernet_area_codes = dict()
        self._free_cores = 0
        for chip in machine.chips:
            key = (chip.x, chip.y)

            # add area codes for ethernets
            ethernet_connected_chip = machine.get_chip_at(
                chip.nearest_ethernet_x, chip.nearest_ethernet_y)
            ethernet_area_code = ethernet_connected_chip.ip_address
            if ethernet_area_code not in self._ethernet_area_codes.keys():
                self._ethernet_area_codes[ethernet_area_code] = set()
            self._ethernet_area_codes[ethernet_area_code].add(key)

            # add chips to placements avilable
            self._placements_available[key] = set()
            for processor in chip.processors:
                if not processor.is_monitor or chip.virtual:
                    self._placements_available[key].add(processor.processor_id)
                    self._free_cores += 1

    def assign_core(self, x, y, p):
        """ assigns a core, therefore data structures need to be updated

        :param x: x corod of core being assigned
        :param y: y corod of core being assigned
        :param p: p corod of core being assigned
        :type x: int
        :type y: int
        :type p: int or None
        :return: the triple of x,y ,p thats been assigned.
        :raises PacmanPlaceException: when the chip doesnt exist, or p is
         not avilable
        """
        key = (x, y)

        # check key exists
        if key not in self._placements_available:
            raise exceptions.PacmanPlaceException(
                "cannot assign to chip {}:{} as the chip does not exist for "
                "placement".format(x, y))

        # locate processor list
        processors_available = self._placements_available[key]
        if p is None:

            # locate first available
            p = self._locate_first_available(x, y)
        else:

            # check that there's a processor available
            if p not in processors_available:
                raise exceptions.PacmanPlaceException(
                    "cannot assign to processor {} in chip {}:{} as the "
                    "processor has already been assigned")

        # update processor
        processors_available.remove(p)
        self._free_cores -= 1
        return x, y, p

    def unassign_core(self, x, y, p):
        """ assigns a core, therefore data structures need to be updated

        :param x: x corod of core being unassigned
        :param y: y corod of core being unassigned
        :param p: p corod of core being unassigned
        :type x: int
        :type y: int
        :type p: int
        :return: the triple of x,y ,p thats been assigned.
        :raises PacmanPlaceException: when the core has already been unassigned
        """
        key = (x, y)
        #check key exists
        if not key in self._placements_available:
            raise exceptions.PacmanPlaceException(
                "cannot unassign to chip {}:{} as the chip does not exist for "
                "placement".format(x, y))
        processor_list = self._placements_available[key]
        if p not in processor_list:
            processor_list.add(p)
        else:
            raise exceptions.PacmanPlaceException(
                "cannot unassign processor {} in chip {}:{} as the "
                "processor has already been unassigned")
        self._free_cores += 1

    def has_available_cores_left(self, x, y, p):
        """

        :param x: x corod of core being unassigned
        :param y: y corod of core being unassigned
        :param p: p corod of core being unassigned
        :type x: int
        :type y: int
        :type p: int or None
        :return: true or false based on if there are cores avilable
        :raises PacmanPlaceException: if the chip doest exist in the tracker
        """
        key = (x, y)
        if key not in self._placements_available.keys():
            raise exceptions.PacmanPlaceException(
                "cannot determine if the chip {}:{} has free processors, as"
                " the chip does not exist in the machine".format(x, y))
        else:
            available_cores = self._placements_available[key]
            if p is None:
                return len(available_cores) > 0
            else:
                return p in available_cores

    def ethernet_area_code_has_avilable_cores_left(self, ethernet_area_code):
        """
        :param ethernet_area_code: the ipaddress used to check if any cores
        still avilable for placement
        :return: true or false
        """
        if ethernet_area_code not in self._ethernet_area_codes.keys():
            raise exceptions.PacmanConfigurationException(
                "this area code does not exist, please rectify and try again")

        for chip_key in self._ethernet_area_codes[ethernet_area_code]:
            if self.has_available_cores_left(chip_key[0], chip_key[1], None):
                return True
        return False

    def ethernet_area_code_contains_chip(
            self, ethernet_area_code, chip_x, chip_y):
        """
        helper method for determining if a chip exists in a given area code

        :param ethernet_area_code: the area code for this ethernet
        :type ethernet_area_code: str
        :param chip_x: the x coord of the chip in question
        :type chip_x: int
        :param chip_y: the y coord of the chip in question
        :type chip_y: int
        :return: a bool if the chip exists in this etehrnet area code
        :raises PacmanConfigurationException: if the area code does not exist.
        """
        if ethernet_area_code not in self._ethernet_area_codes.keys():
            raise exceptions.PacmanConfigurationException(
                "this area code does not exist, please rectify and try again")
        key = (chip_x, chip_y)
        if key not in self._ethernet_area_codes[ethernet_area_code]:
            return False
        else:
            return True

    def get_chips_in_ethernet_area_code(self, ethernet_area_code):
        """ helper method for locating chips in a given ethernet area code

        :param ethernet_area_code: the ethernet area code to which the list of
        chips is to be located
        :type ethernet_area_code: str
        :return: a iterable of chips.
        raises PacmanConfigurationException: if the area code does not exist.
        """
        if ethernet_area_code not in self._ethernet_area_codes.keys():
            raise exceptions.PacmanConfigurationException(
                "this area code does not exist, please rectify and try again")
        return self._ethernet_area_codes[ethernet_area_code]

    def _locate_first_available(self, x, y):
        """
        :param x: x corod of core being unassigned
        :param y: y corod of core being unassigned
        :type x: int
        :type y: int
        :return: a processor id
        :rtype: int or none
        :raises PacmanPlaceException: if the chip does not exist in the tracker
        """
        key = (x, y)

        # check key exists
        if key not in self._placements_available:
            raise exceptions.PacmanPlaceException(
                "cannot assign to chip {}:{} as the chip does not exist for "
                "placement".format(x, y))
        if len(self._placements_available[key]) > 0:
            return next(iter(self._placements_available[key]))
        return None

    @property
    def ethernet_area_codes(self):
        """ property for ethernet area codes

        :return:
        """
        return self._ethernet_area_codes
