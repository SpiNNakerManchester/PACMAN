from spinn_machine.tags.iptag import IPTag
from spinn_machine.tags.reverse_iptag import ReverseIPTag

from pacman import exceptions

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

        :param tag:
        :param board_address:
        :param address:
        :param port:
        :param strip_sdp:
        :return:
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

    def add_reverse_ip_tag(
            self, tag, board_address, port, x, y, p, port_num,
            partitioned_vertex):
        """ adds a reverse iptag into the lists

        :param tag:
        :param board_address:
        :param port:
        :param x:
        :param y:
        :param p:
        :param port_num:
        :return:
        """

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
        """

        :param tag:
        :return:
        """
        if tag not in self._tag_to_board_mapping.keys():
            return None
        else:
            return self._tag_to_board_mapping[tag]

    def has_tags_for_board(self, board_address):
        """

        :param board_address:
        :return:
        """
        if board_address in self._boards_used:
            return True
        else:
            return False

    def get_tags_for_board(self, board_address):
        """

        :param board_address:
        :return:
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
        """

        :param board_address:
        :return:
        """
        if board_address in self._iptags.keys():
            return True
        return False

    def get_ip_tags_for_board(self, board_address):

        """

        :param board_address:
        :return:
        """
        if board_address in self._iptags.keys():
            return self._iptags[board_address]
        return None

    def has_reverse_iptags_for_board(self, board_address):
        """

        :param board_address:
        :return:
        """
        if board_address in self._reverse_ip_tags.keys():
            return True
        return False

    def get_reverse_ip_tags_for_board(self, board_address):

        """

        :param board_address:
        :return:
        """
        if board_address in self._reverse_ip_tags.keys():
            return self._reverse_ip_tags[board_address]
        return None

    def get_iptag_mapping_for(self, port, ip_address):
        """

        :param port:
        :param ip_address:
        :return:
        """
        key = (ip_address, port)
        if key not in self._port_ip_address_map.keys():
            return None
        else:
            return self._port_ip_address_map[key]

    def contains_iptag_mapping_for(self, port, ip_address):
        """

        :param port:
        :param ip_address:
        :return:
        """
        key = (ip_address, port)
        if key not in self._port_ip_address_map.keys():
            return False
        return True

    def get_reverse_iptag_mapping_for(self, x, y, p, port):
        """

        :param x:
        :param y:
        :param p:
        :param port:
        :return:
        """
        key = (x, y, p, port)
        if key not in self._port_x_y_p_mapping.keys():
            return None
        else:
            return self._port_x_y_p_mapping[key]

    def get_board_addresses_with_tags(self):
        """

        :return:
        """
        return self._boards_used

    def contains_reverse_iptag_mapping_for(self, x, y, p, port):
        """

        :param x:
        :param y:
        :param p:
        :param port:
        :return:
        """
        key = (x, y, p, port)
        if key not in self._port_x_y_p_mapping.keys():
            return False
        return True

    def get_tag_for_partitioned_vertex(self, partitioned_vertex_label):
        """

        :param partitioned_vertex_label:
        :return:
        """
        return self._partitioned_vertex_label_to_iptag_mapping[
            partitioned_vertex_label]

