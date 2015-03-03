from pacman.model.constraints.abstract_constraints.abstract_utility_constraint import \
    AbstractUtilityConstraint


class VertexRequiresVirtualChipInMachineConstraint(AbstractUtilityConstraint):
    """ A constraint which indicates that a vertex has a requirement for some
    multicast packets to be trnasmitted at given times
    itself to a multicast source
    """

    def __init__(self, virtual_chip_coords, connected_to_chip_coords,
                 connected_chip_link_id):
        """

        :param virtual_chip_coords: The virtual coords of the virtual chip
        :param connected_to_chip_coords: the chip coords to which the virtual \
        chip connects to
        :param connected_chip_link_id: the link id that the virtual chip \
        connects to the real chip
        :type virtual_chip_coords: tuple with x and y
        :type connected_to_chip_coords:  tuple with x and y
        :type connected_chip_link_id: int
        :raise None: does not raise any known exceptions
        """
        AbstractUtilityConstraint.__init__(
            self, "AbstractConstrainedVertex Requires a virtual chip in the "
                  "machine with coords {}:{} connected to the real chip at "
                  "coords {}:{} on link {}"
                  .format(virtual_chip_coords['x'], virtual_chip_coords['y'],
                          connected_to_chip_coords['x'],
                          connected_to_chip_coords['y'],
                          connected_chip_link_id))
        self._virtual_chip_coords = virtual_chip_coords
        self._connected_to_chip_coords = connected_to_chip_coords
        self._connected_chip_link_id = connected_chip_link_id

    def is_utility_constraint(self):
        return True

    @property
    def virtual_chip_coords(self):
        """ the virtual chip coords

        :return: the virtual chip coords
        :rtype: tuple
        :raise None: does not raise any known exceptions
        """
        return self._virtual_chip_coords

    @property
    def connected_to_chip_coords(self):
        """ the chip to which the virutal chip connects to

        :return: the chip to which the virutal chip connects to
        :rtype: tuple
        :raise None: does not raise any known exceptions
        """
        return self._connected_to_chip_coords

    @property
    def connected_to_chip_link_id(self):
        """ the link on the chip to which the virutal chip connects to

        :return: the link on the chip to which the virutal chip connects to
        :rtype: tuple
        :raise None: does not raise any known exceptions
        """
        return self._connected_chip_link_id
