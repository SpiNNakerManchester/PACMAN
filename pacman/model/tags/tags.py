from pacman.exceptions import PacmanInvalidParameterException


class Tags(object):
    """ Represents assigned IP Tag and Reverse IP Tags
    """

    def __init__(self):

        # Mapping of (board address, tag) to IPTag
        self._ip_tags = dict()

        # Mapping of (board address, tag) to ReverseIPTag
        self._reverse_ip_tags = dict()

        # Mapping of partitioned vertex to list of IPTag
        self._ip_tags_by_vertex = dict()

        # Mapping of partitioned vertex to list of ReverseIPTag
        self._reverse_ip_tags_by_vertex = dict()

        # Set of ports already assigned on a board
        self._ports_assigned = set()

    def add_ip_tag(self, ip_tag, partitioned_vertex):
        """ Add an IP tag

        :param ip_tag: The tag to add
        :type ip_tag: :py:class:`spinn_machine.tags.iptag.IPTag`
        :param partitioned_vertex: The partitioned vertex by which the tag\
                    is to be used
        :type partitioned_vertex:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :raises PacmanInvalidParameterException:
                    * If the combination of (board-address, tag) has already\
                      been assigned to an IP tag with different properties
                    * If the combination of (board-address, tag) has already\
                      been assigned to a reverse IP tag
        """

        if (ip_tag.board_address, ip_tag.tag) in self._ip_tags:
            existing_tag = self._ip_tags[(ip_tag.board_address, ip_tag.tag)]
            if (existing_tag.ip_address != ip_tag.ip_address
                    or existing_tag.port != ip_tag.port
                    or existing_tag.strip_sdp != ip_tag.strip_sdp):
                raise PacmanInvalidParameterException(
                    "ip_tag", str(ip_tag),
                    "The tag specified has already been assigned with"
                    " different properties: {}".format(existing_tag))

        if (ip_tag.board_address, ip_tag.tag) in self._reverse_ip_tags:
            raise PacmanInvalidParameterException(
                "ip_tag", ip_tag,
                "The tag has already been assigned to a reverse IP tag on"
                " the given board")

        self._ip_tags[(ip_tag.board_address, ip_tag.tag)] = ip_tag
        if partitioned_vertex not in self._ip_tags_by_vertex:
            self._ip_tags_by_vertex[partitioned_vertex] = list()
        self._ip_tags_by_vertex[partitioned_vertex].append(ip_tag)

    def add_reverse_ip_tag(self, reverse_ip_tag, partitioned_vertex):
        """ Add a reverse iptag

        :param reverse_ip_tag: The tag to add
        :type reverse_ip_tag:\
                    :py:class:`spinn_machine.tags.reverse_iptag.ReverseIPTag`
        :param partitioned_vertex: The partitioned vertex by which the tag\
                    is to be used
        :type partitioned_vertex:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :raises PacmanInvalidParameterException:
                    * If the combination of (board-address, tag) has already\
                      been assigned to an IP tag or Reverse IP tag
                    * If the port of the tag has already been assigned on\
                      the given board-address
        """

        if ((reverse_ip_tag.board_address, reverse_ip_tag.tag) in self._ip_tags
                or (reverse_ip_tag.board_address, reverse_ip_tag.tag)
                in self._reverse_ip_tags):
            raise PacmanInvalidParameterException(
                "reverse_ip_tag", reverse_ip_tag,
                "The tag has already been assigned on the given board")

        if (reverse_ip_tag.board_address,
                reverse_ip_tag.port) in self._reverse_ip_tags:
            raise PacmanInvalidParameterException(
                "reverse_ip_tag", reverse_ip_tag,
                "The port has already been assigned on the given board")

        self._reverse_ip_tags[(reverse_ip_tag.board_address,
                               reverse_ip_tag.tag)] = reverse_ip_tag
        if partitioned_vertex not in self._reverse_ip_tags_by_vertex:
            self._reverse_ip_tags_by_vertex[partitioned_vertex] = list()
        self._reverse_ip_tags_by_vertex[partitioned_vertex].append(
            reverse_ip_tag)
        self._ports_assigned.add(
            (reverse_ip_tag.board_address, reverse_ip_tag.port))

    @property
    def ip_tags(self):
        """ The IPTags assigned

        :return: iterable of IPTag
        :rtype: iterable of :py:class:`spinn_machine.tags.iptag.IPTag`
        """
        return self._ip_tags.itervalues()

    @property
    def reverse_ip_tags(self):
        """ The ReverseIPTags assigned

        :return: iterable of ReverseIPTag
        :rtype: iterable of \
                    :py:class:`spinn_machine.tags.reverse_iptag.ReverseIPTag`
        """
        return self._reverse_ip_tags.itervalues()

    def get_ip_tags_for_vertex(self, partitioned_vertex):
        """ Get the IP Tags assigned to a given partitioned vertex

        :param partitioned_vertex: The partitioned vertex to get the tags for
        :type partitioned_vertex:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :return: An iterable of IPTag or None if the vertex has no tags
        :rtype: iterable of :py:class:`spinn_machine.tags.iptag.IPTag`
        """
        if partitioned_vertex not in self._ip_tags_by_vertex:
            return None
        return self._ip_tags_by_vertex[partitioned_vertex]

    def get_reverse_ip_tags_for_vertex(self, partitioned_vertex):
        """ Get the Reverse IP Tags assigned to a given partitioned vertex

        :param partitioned_vertex: The partitioned vertex to get the tags for
        :type partitioned_vertex:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :return: An iterable of ReverseIPTag or None if the vertex has no tags
        :rtype: iterable of \
                    :py:class:`spinn_machine.tags.reverse_iptag.ReverseIPTag`
        """
        if partitioned_vertex not in self._reverse_ip_tags_by_vertex:
            return None
        return self._reverse_ip_tags_by_vertex[partitioned_vertex]
