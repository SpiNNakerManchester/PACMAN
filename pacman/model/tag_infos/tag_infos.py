from spinn_machine.tags.iptag import IPTag
from spinn_machine.tags.reverse_iptag import ReverseIPTag

from pacman import exceptions

class TagInfos(object):

    def __init__(self):
        self._iptags = dict()
        self._reverse_ip_tags = dict()
        self._boards_used = list()

    def add_iptag(self, tag, board_address, address, port, strip_sdp):
        """ adds a iptag into the lists

        :param tag:
        :param board_address:
        :param address:
        :param port:
        :param strip_sdp:
        :return:
        """
        iptag = IPTag(address, port, tag, strip_sdp)
        if board_address not in self._iptags.keys():
            self._iptags[board_address] = list()
        self._iptags[board_address].append(iptag)
        if board_address not in self._boards_used:
            self._boards_used.append(board_address)

    def add_reverse_ip_tag(self, tag, board_address, port, x, y, p, port_num):
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
        reverse_iptag = ReverseIPTag(port, tag, x, y, p, port_num)
        if board_address not in self._reverse_ip_tags.keys():
            self._reverse_ip_tags[board_address] = list()
        self._reverse_ip_tags[board_address].append(reverse_iptag)
        if board_address not in self._boards_used:
            self._boards_used.append(board_address)

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


