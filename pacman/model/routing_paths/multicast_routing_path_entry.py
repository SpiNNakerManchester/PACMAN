"""
MulticastRoutingPathEntry
"""

# pacman imports
from pacman import exceptions


class MulticastRoutingPathEntry(object):
    """ An entry in a path of a multicast route
    """

    def __init__(self, router_x, router_y, edge, out_going_links,
                 outgoing_processors, incoming_processor=None,
                 incoming_link=None):
        """

        :param router_x: the x coord of the router this is associated with
        :type router_x: int
        :param router_y: the y coord of the router this is associated with
        :type router_y: int
        :param edge: the partitioned edge this entry is associated with
        :type edge: \
                    :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
        :param out_going_links: the edges this path entry goes down
        :type out_going_links: iterable of ints between 0 and 5
        :param outgoing_processors: the processors this path entry goes to
        :type outgoing_processors: iterable of ints between 0 and 17
        :param incoming_processor:  the direction this entry came from
        :type incoming_processor: int between 0 and 17
        :param incoming_link: the direction this entry came from in link
        :type incoming_link: int between 0 and 5
        :return:
        """
        self._router_x = router_x
        self._router_y = router_y
        self._edge = edge
        if isinstance(out_going_links, int):
            self._out_going_links = list()
            self._out_going_links.append(out_going_links)
        else:
            self._out_going_links = out_going_links

        if isinstance(outgoing_processors, int):
            self._out_going_processors = list()
            self._out_going_processors.append(outgoing_processors)
        else:
            self._out_going_processors = outgoing_processors

        self._incoming_link = incoming_link
        self._incoming_processor = incoming_processor

        if (self._incoming_link is not None and
                self._incoming_processor is not None):
            raise exceptions.PacmanInvalidParameterException(
                "The incoming direction for a path can only be from either "
                "one link or one processors, not both",
                str(self._incoming_link), str(self._incoming_processor))
        if (self._incoming_link is not None and
                not isinstance(self._incoming_link, int)):
            raise exceptions.PacmanInvalidParameterException(
                "The incoming direction for a path can only be from either "
                "one link or one processors, not both",
                str(self._incoming_link), str(self._incoming_processor))

    @property
    def router_x(self):
        """ Router x coordinate
        :return:
        """
        return self._router_x

    @property
    def router_y(self):
        """ Router y coordinate
        :return:
        """
        return self._router_y

    @property
    def edge(self):
        """ The partitioned edge of the entry
        :return:
        """
        return self._edge

    @property
    def out_going_processors(self):
        """ The destination processors of the entry
        :return:
        """
        if self._out_going_processors is None:
            return ()
        else:
            return self._out_going_processors

    @property
    def out_going_links(self):
        """ The destination links of the entry
        :return:
        """
        if self._out_going_links is None:
            return ()
        else:
            return self._out_going_links

    @property
    def incoming_link(self):
        """ The source link for this path entry
        :return:
        """
        return self._incoming_link

    @property
    def incoming_processor(self):
        """ The source processor
        :return:
        """
        return self._incoming_processor

    @property
    def defaultable(self):
        """ The defaultable status of the entry
        :return:
        """
        return self._is_defaultable()

    def add_out_going_direction_link(self, direction):
        """ Add a new outgoing direction link into the entry

        :param direction: the new outgoing direction
        :return:
        """
        if direction not in self._out_going_links and 0 < direction <= 5:
            self._out_going_links.append(direction)
        else:
            raise exceptions.PacmanAlreadyExistsException(
                "the link {} already exists in the mutlicast-"
                "routing-path-entry".format(direction), str(direction))

    def add_out_going_direction_processor(self, direction):
        """ Add a new outgoing direction processor into the entry

        :param direction: the new outgoing direction
        :return:
        """
        if direction not in self._out_going_processors and 0 < direction <= 5:
            self._out_going_processors.append(direction)
        else:
            raise exceptions.PacmanAlreadyExistsException(
                "the processor {} already exists in the mutlicast-"
                "routing-path-entry".format(direction), str(direction))

    def add_in_coming_processor_direction(self, procesor_id):
        """ Add a processor to the incoming direction

        :param procesor_id: the processor to add to the incoming list
        :return:
        """
        if self._incoming_link is not None:
            raise exceptions.PacmanInvalidParameterException(
                "there is already a link for incoming, you can only have one "
                "incoming direction", str(self._incoming_link), "already set")
        if (self._incoming_processor is not None and
                self._incoming_processor != procesor_id):
            raise exceptions.PacmanInvalidParameterException(
                "there is already a processor for incoming, you can only have "
                "one incoming direction", str(self._incoming_processor),
                "already set")
        else:
            self._incoming_processor = procesor_id

    def _is_defaultable(self):
        """

        :return: if this entry is defaultable or not
        :rtype: bool
        """
        if (isinstance(self._incoming_link, int) and
                self._incoming_processor is None and
                isinstance(self._out_going_links, int) and
                self._out_going_processors is None):
            if self._incoming_link == 0 and self.out_going_links == 3:
                return True
            elif self._incoming_link == 1 and self.out_going_links == 4:
                return True
            elif self._incoming_link == 2 and self.out_going_links == 5:
                return True
            elif self._incoming_link == 3 and self._out_going_links == 0:
                return True
            elif self._incoming_link == 4 and self._out_going_links == 1:
                return True
            elif self._incoming_link == 5 and self._out_going_links == 2:
                return True
            else:
                return False
        else:
            return False
