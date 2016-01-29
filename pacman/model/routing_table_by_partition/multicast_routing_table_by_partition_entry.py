"""
MulticastRoutingTableByPartitionEntry
"""

# pacman imports
from pacman import exceptions


class MulticastRoutingTableByPartitionEntry(object):
    """ An entry in a path of a multicast route
    """

    def __init__(self, out_going_links, outgoing_processors,
                 incoming_processor=None, incoming_link=None):
        """

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
        if isinstance(out_going_links, int):
            self._out_going_links = set()
            self._out_going_links.add(out_going_links)
        else:
            if out_going_links is not None:
                self._out_going_links = set(out_going_links)
            else:
                self._out_going_links = set()

        if isinstance(outgoing_processors, int):
            self._out_going_processors = set()
            self._out_going_processors.add(outgoing_processors)
        else:
            if outgoing_processors is not None:
                self._out_going_processors = set(outgoing_processors)
            else:
                self._out_going_processors = set()

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
    def out_going_processors(self):
        """ The destination processors of the entry
        :return:
        """
        return self._out_going_processors

    @property
    def out_going_links(self):
        """ The destination links of the entry
        :return:
        """
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
            self._out_going_links.add(direction)
        else:
            raise exceptions.PacmanAlreadyExistsException(
                "the link {} already exists in the multicast-"
                "routing-path-entry".format(direction), str(direction))

    def add_out_going_direction_processor(self, direction):
        """ Add a new outgoing direction processor into the entry

        :param direction: the new outgoing direction
        :return:
        """
        if direction not in self._out_going_processors and 0 < direction <= 5:
            self._out_going_processors.add(direction)
        else:
            raise exceptions.PacmanAlreadyExistsException(
                "the processor {} already exists in the multicast-"
                "routing-path-entry".format(direction), str(direction))

    def add_in_coming_processor_direction(self, processor_id):
        """ Add a processor to the incoming direction

        :param processor_id: the processor to add to the incoming list
        :return:
        """
        if self._incoming_link is not None:
            raise exceptions.PacmanInvalidParameterException(
                "there is already a link for incoming, you can only have one "
                "incoming direction", str(self._incoming_link), "already set")
        if (self._incoming_processor is not None and
                self._incoming_processor != processor_id):
            raise exceptions.PacmanInvalidParameterException(
                "there is already a processor for incoming, you can only have "
                "one incoming direction", str(self._incoming_processor),
                "already set")
        else:
            self._incoming_processor = processor_id

    def merge_entry(self, other):
        """
        merges the results and returns a new
        MulticastRoutingTableByPartitionEntry
        :param other: the MulticastRoutingTableByPartitionEntry to merge into
        this one
        :return: a merged MulticastRoutingTableByPartitionEntry
        """
        if not isinstance(other, MulticastRoutingTableByPartitionEntry):
            raise exceptions.PacmanInvalidParameterException(
                "other", "type error",
                "The other parameter is not a instance of "
                "MulticastRoutingTableByPartitionEntry, and therefore cannot "
                "be merged.")
        else:
            # validate fixed things
            if (self._incoming_processor is None and
                    other.incoming_processor is None):
                valid_incoming_processor = None
            elif (self._incoming_processor is not None and
                    other._incoming_processor is None):
                valid_incoming_processor = self._incoming_processor
            elif (self._incoming_processor is None
                    and other.incoming_processor is not None):
                valid_incoming_processor = other.incoming_processor
            elif self._incoming_processor == other._incoming_processor:
                valid_incoming_processor = self._incoming_processor
            else:
                raise exceptions.PacmanInvalidParameterException(
                    "incoming_processor", "invalid merge", 
                    "The two MulticastRoutingTableByPartitionEntry have "
                    "different incoming_processors, and so cant be merged")

            if (self._incoming_link is None and
                    other.incoming_link is None):
                valid_incoming_link = None
            elif (self._incoming_link is not None and
                    other._incoming_link is None):
                valid_incoming_link = self._incoming_link
            elif (self._incoming_link is None
                    and other.incoming_link is not None):
                valid_incoming_link = other.incoming_link
            elif self._incoming_link == other._incoming_link:
                valid_incoming_link = self._incoming_link
            else:
                raise exceptions.PacmanInvalidParameterException(
                    "incoming_link", "invalid merge", 
                    "The two MulticastRoutingTableByPartitionEntry have "
                    "different incoming_links, and so cant be merged")

            # merge merge-able things
            merged_outgoing_processors = \
                self._out_going_processors.union(other._out_going_processors)
            merged_outgoing_links = \
                self._out_going_links.union(other._out_going_links)

            return MulticastRoutingTableByPartitionEntry(
                merged_outgoing_links, merged_outgoing_processors,
                valid_incoming_processor, valid_incoming_link)

    def _is_defaultable(self):
        """

        :return: if this entry is defaultable or not
        :rtype: bool
        """
        if (isinstance(self._incoming_link, int) and
                self._incoming_processor is None and
                len(self._out_going_links) == 1 and
                len(self._out_going_processors) == 0):
            outgoing_link = next(iter(self._out_going_links))
            if self._incoming_link == 0 and outgoing_link == 3:
                return True
            elif self._incoming_link == 1 and outgoing_link == 4:
                return True
            elif self._incoming_link == 2 and outgoing_link == 5:
                return True
            elif self._incoming_link == 3 and outgoing_link == 0:
                return True
            elif self._incoming_link == 4 and outgoing_link == 1:
                return True
            elif self._incoming_link == 5 and outgoing_link == 2:
                return True
            else:
                return False
        else:
            return False

    def __repr__(self):
        return "{}:{}:{}:{}:{}".format(
            self._incoming_link, self._incoming_processor,
            self._is_defaultable(), self._out_going_links,
            self._out_going_processors)
