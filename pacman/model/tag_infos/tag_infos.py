from spinn_machine.tags.iptag import IPTag
from spinn_machine.tags.reverse_iptag import ReverseIPTag
from pacman import exceptions
from spinn_machine.tags.abstract_tag import AbstractIPTAG


class TagInfos(object):

    def __init__(self):
        self._iptags = dict()
        self._reverse_ip_tags = dict()
        self._boards_used = list()
        self._tag_to_board_mapping = dict()
        self._port_ip_address_map = dict()
        self._port_x_y_p_mapping = dict()
        self._partitioned_vertex_label_to_iptag_mapping = dict()

    def add_iptag(self, tag, board_address, address, port, strip_sdp,
                  partitioned_vertex_label):
        """ adds a iptag into the lists

        :param tag: the tag id of the iptag
        :param board_address: the board_address of the iptag
        :param address: the ipaddress of the iptag
        :param port: the port_number of the iptag
        :param strip_sdp: the stripe sdp parameter used in the iptag to decide
        if when outputting packets from spinnaker if they should have their
        sdp header removed or not
        :type tag: int
        :type board_address: str
        :type address: str
        :type port: int
        :type strip_sdp: bool
        :return None: this mwethod does not return anything
        :raises PacmanConfigurationException: if the board-address is none,
        this is becuase all iptags need a board address to associate it
        with a iptag table on the machine.
        """
        if board_address is None:
            raise exceptions.PacmanConfigurationException(
                "At this point, the board address cannot be None. This means"
                "something is wrong with the tag_allocator. Please fix and "
                "try again")

        iptag = IPTag(address, port, tag, strip_sdp)
        if board_address not in self._iptags.keys():
            self._iptags[board_address] = list()
        self._iptags[board_address].append(iptag)

        # handle board addresses used mapping
        if board_address not in self._boards_used:
            self._boards_used.append(board_address)

        # handle port_ip-address mapping
        port_ip_address_key = (address, port)
        if port_ip_address_key not in self._port_ip_address_map.keys():
            self._port_ip_address_map[port_ip_address_key] = list()
        self._port_ip_address_map[port_ip_address_key].append(iptag)

        # handle tag to board mapping
        self._tag_to_board_mapping[iptag] = board_address

        # handle partitioned vertex to tag mapping
        self._partitioned_vertex_label_to_iptag_mapping[
            partitioned_vertex_label] = iptag

    def add_reverse_ip_tag(self, tag, board_address, port, x, y, p, port_num):
        """ adds a reverse iptag into the lists which represent the tag-info
        object

        :param tag: the tag id for this reverse ip tag.
        :param board_address: the board address to which this reverse ip tag
        is associated
        :param port: the port number used to associate this reverse_iptag
        :param x: the x coord for the core that packets being sent via this
         reverse iptag go to.
        :param y: the y coord for the core that packets being sent via this
         reverse iptag go to.
        :param p: the p coord for the core that packets being sent via this
         reverse iptag go to.
        :param port_num: a port_num paramter that is added to the sdp packet
        being injected to a core.
        :return None: this method does not return anything
        :raises PacmanConfigurationException: when the board-address is none,
        this is becuase all iptags need a board address to associate it
        with a iptag table on the machine.
        or when there is already a reverse_ip_tag with the same configuration
        inside the tag_info object. This isnt allowed as there should only
        ever be one reverse-iptag to a given core per machine
        NOTE: this limitation may need to be removed"""

        if board_address is None:
            raise exceptions.PacmanConfigurationException(
                "At this point, the board address cannot be None. This means"
                "something is wrong with the tag_allocator. Please fix and "
                "try again")

        reverse_iptag = ReverseIPTag(port, tag, x, y, p, port_num)
        if board_address not in self._reverse_ip_tags.keys():
            self._reverse_ip_tags[board_address] = list()
        self._reverse_ip_tags[board_address].append(reverse_iptag)
        if board_address not in self._boards_used:
            self._boards_used.append(board_address)
        # handle port_ip-address mapping
        port_x_y_z_key = (x, y, p, port)
        if port_x_y_z_key in self._port_x_y_p_mapping.keys():
            raise exceptions.PacmanConfigurationException(
                "this reverse iptag has been built already, please "
                "fix and try again. \n This has likely occured due to some "
                "manglation of the placement algorithum!!!")
        self._port_x_y_p_mapping[port_x_y_z_key] = reverse_iptag

        # handle tag to board mapping
        self._tag_to_board_mapping[reverse_iptag] = board_address

    def get_board_address_from_tag(self, tag):
        """ helper method which returns the board address for a given tag
        (reverse or otherwise)

        :param tag: the tag to which the board address is being seeked.
        :type tag: isntance of
        "spinn_machine.tags.abstract_tag.AbstractTag"
        :return: None if this tag has no board address or the board_address.
        :raises PacmanConfigurationException: if the tag is not of a instance of
         "spinn_machine.tags.abstract_tag.AbstractTag"
        """
        if not isinstance(tag, AbstractIPTAG):
            raise exceptions.PacmanConfigurationException(
                "The tag is not a valid object (it is not a subclass "
                "of AbstractIPTAG) and therefore the tag info object cannot "
                "search for its board-address")
        if tag not in self._tag_to_board_mapping.keys():
            return None
        else:
            return self._tag_to_board_mapping[tag]

    def has_tags_for_board(self, board_address):
        """ helper method which informs the parent function if this
        tag_info object contains tags for a given board addres

        :param board_address: the board-address to check if there are
         tags allocated to it.
         :type board_address: str
        :return: True if there are tags on this board or False if not.
        :raises None: this method does not raise any known exceptions
        """
        if board_address in self._boards_used:
            return True
        else:
            return False

    def get_tags_for_board(self, board_address):
        """ getter for tags on a given board

        :param board_address: the board-address to retrieve tags for
        :type board_address: str
        :return: a iterable of the tags allocated to this board
        :rtype: iterable of "spinn_machine.tags.abstract_tag.AbstractTag"
        :raises PacmanInvalidParameterException: if the board-address is not
        one which has any tags on it.
        """
        if board_address not in self._boards_used:
            raise exceptions.PacmanInvalidParameterException(
                "There are no tags for this board address. please fix and try"
                " again", "board_address", "doesnt exist")
        else:
            tags = list()
            if board_address in self._iptags.keys():
                iptag_tags = self._iptags[board_address]
                tags.extend(iptag_tags)
            if board_address in self._reverse_ip_tags.keys():
                reverse_ip_tags = self._reverse_ip_tags[board_address]
                tags.extend(reverse_ip_tags)
            return tags

    def has_iptags_for_board(self, board_address):
        """ helper method which allows parent functions to knwo if a
         board-address contains iptags

        :param board_address: the board to which the search for iptags is
         to be taken
        :return: True if there are iptags and False otherwsie
        :rtype: bool
        :raises None: this method does not raise any known exceptions
        """
        if board_address in self._iptags.keys():
            return True
        return False

    def get_ip_tags_for_board(self, board_address):
        """ getter for iptags for a given board

        :param board_address: the board to which iptags are to be returned
        :type board_address: str
        :return: iterable of iptags associated with the board-address or none
        :rtype: None or iterrable of "spinn_machine.tags.iptag.IPTAG"
        """
        if board_address in self._iptags.keys():
            return self._iptags[board_address]
        return None

    def has_reverse_iptags_for_board(self, board_address):
        """ helper method which checks if a board has any reverse iptags

        :param board_address: the board to which iptags are to be returned
        :type board_address: str
        :return: True if there are reverse_iptags and False otherwsie
        :rtype: bool
        :raises None: this method does not raise any known exceptions
        """
        if board_address in self._reverse_ip_tags.keys():
            return True
        return False

    def get_reverse_ip_tags_for_board(self, board_address):
        """getter for reverse_iptags for a given board

        :param board_address: the board to which reverse_iptags are to be
        returned
        :type board_address: str
        :return: iterable of reverse_iptags associated with the board-address
        or none
        :rtype: None or iterrable of
        "spinn_machine.tags.reverse_iptag.ReverseIPTAG"
        """
        if board_address in self._reverse_ip_tags.keys():
            return self._reverse_ip_tags[board_address]
        return None

    def get_iptag_for(self, port, ip_address):
        """ getter method for all iptags which are associated with a port and
        iptaddress over the entire machine

        :param port: the portnumber to which all iptags must go to,
        to count in the return list.
        :type port: int
        :param ip_address: the ipaddress to which all iptags must contain
        to count in the return list.
        :return: iterable of iptags associated with the board-address
        or none
        :rtype: None or iterable of "spinn_machine.tags.iptag.Iptag"
        :raises None: This method does not raise any known exceptions
        """
        key = (ip_address, port)
        if key not in self._port_ip_address_map.keys():
            return None
        else:
            return self._port_ip_address_map[key]

    def contains_iptag_for(self, port, ip_address):
        """ helper method which allows parent functions to know if there are
        iptags somewhere on the machine which are associated with a port and
        ipaddress

        :param port: the portnumber to whcih a iptags need to be associed
        with for the method to return true
        :param ip_address: the ipaddress to which a iptag must be associated
        with for the method to return true
        :type port: int
        :type ip_address: str
        :return: True if there are iptags which meet the requirements.
        False otherwise
        :rtype: bool
        :raises None: this method does not raise any known exceptions
        """
        key = (ip_address, port)
        if key not in self._port_ip_address_map.keys():
            return False
        return True

    def get_reverse_iptag_for(self, x, y, p, port):
        """ geter method for locating a reverse_iptag for a given core on a
        given port

        :param x: the x coordinate for the core to which teh reverse iptag
         must be linked to
         :type x: int
        :param y: the y coordinate for the core to which teh reverse iptag
         must be linked to
         :type y: int
        :param p: the p coordinate for the core to which teh reverse iptag
         must be linked to
         :type p: int
        :param port: the port number to which the reverse_iptag must be linked
        to
        :type port: int
        :return: either the reverse iptag or none if no reverse iptag with these
        parameters exists currently
        :rtype None or a instance of
        "spinn_machine.tags.reverse_iptag.ReverseIptag"
        :raises None: this method does not raise any known exceptions
        """
        key = (x, y, p, port)
        if key not in self._port_x_y_p_mapping.keys():
            return None
        else:
            return self._port_x_y_p_mapping[key]

    def get_board_addresses_with_tags(self):
        """ returns a list of board addresses to which there are tags allocated

        :return: the list of board to which there are tags allocated
        :rtype iterator of str
        :raises None: this method does not raise any known exceptions
        """
        return self._boards_used

    def contains_reverse_iptag_for(self, x, y, p, port):
        """ checker method to allow other functions to check if there is a
        reverse iptag associated with a given port already exists within the
        tag_info object.

        :param x: the x coordinate for the core to check for the reverse_iptag.
        :param y: the y coordinate for the core to check for the reverse_iptag.
        :param p: the p coordinate for the core to check for the reverse_iptag.
        :param port: the port number of the expected reverse_ip_tag
        :type x: int
        :type y: int
        :type p: int
        :type port: int
        :return: True or False given if there is a reverseiptag which that
        mapping already in the taginfo object
        :rtype: bool
        :raises None: this method does not raise any known exceptions
        """
        key = (x, y, p, port)
        if key not in self._port_x_y_p_mapping.keys():
            return False
        return True

    def get_tag_for_partitioned_vertex(self, partitioned_vertex_label):
        """ returns a iptag given a partitioned_vertex_label

        :param partitioned_vertex_label: the label of the partitioned_vertex
        to locate the iptag for
        :return: a IPTag which is associated with this partitioned_vertex_label
        or None if there is no mapping
        :raises None: this method does not raise any known exceptions
        """
        if (partitioned_vertex_label in
                self._partitioned_vertex_label_to_iptag_mapping.keys()):
            return self._partitioned_vertex_label_to_iptag_mapping[
                partitioned_vertex_label]
        return None