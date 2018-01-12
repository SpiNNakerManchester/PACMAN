# pacman imports
from pacman.exceptions import PacmanInvalidParameterException


class MulticastRoutingTableByPartitionEntry(object):
    """ An entry in a path of a multicast route
    """

    __slots__ = [
        # the edges this path entry goes down
        "_out_going_links",

        # the processors this path entry goes to
        "_out_going_processors",

        # the direction this entry came from in link
        "_incoming_link",

        # the direction this entry came from
        "_incoming_processor"
    ]

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
        """
        if isinstance(out_going_links, int):
            self._out_going_links = set()
            self._out_going_links.add(out_going_links)
        elif out_going_links is not None:
            self._out_going_links = set(out_going_links)
        else:
            self._out_going_links = set()

        if isinstance(outgoing_processors, int):
            self._out_going_processors = set()
            self._out_going_processors.add(outgoing_processors)
        elif outgoing_processors is not None:
            self._out_going_processors = set(outgoing_processors)
        else:
            self._out_going_processors = set()

        self._incoming_link = incoming_link
        self._incoming_processor = incoming_processor

        if (self._incoming_link is not None and
                self._incoming_processor is not None):
            raise PacmanInvalidParameterException(
                "The incoming direction for a path can only be from either "
                "one link or one processors, not both",
                str(self._incoming_link), str(self._incoming_processor))
        if (self._incoming_link is not None and
                not isinstance(self._incoming_link, int)):
            raise PacmanInvalidParameterException(
                "The incoming direction for a path can only be from either "
                "one link or one processors, not both",
                str(self._incoming_link), str(self._incoming_processor))

    @property
    def out_going_processors(self):
        """ The destination processors of the entry

        """
        return self._out_going_processors

    @property
    def out_going_links(self):
        """ The destination links of the entry

        """
        return self._out_going_links

    @property
    def incoming_link(self):
        """ The source link for this path entry

        """
        return self._incoming_link

    @incoming_link.setter
    def incoming_link(self, incoming_link):
        if self._incoming_processor is not None:
            raise Exception(
                "Entry already has an incoming processor {}".format(
                    self._incoming_processor))
        if (self._incoming_link is not None and
                self._incoming_link != incoming_link):
            raise Exception(
                "Entry already has an incoming link {}".format(
                    self._incoming_link))
        self._incoming_link = incoming_link

    @property
    def incoming_processor(self):
        """ The source processor
        """
        return self._incoming_processor

    @incoming_processor.setter
    def incoming_processor(self, incoming_processor):
        if (self._incoming_processor is not None and
                self._incoming_processor != incoming_processor):
            raise Exception(
                "Entry already has an incoming processor {}".format(
                    self._incoming_processor))
        if self._incoming_link is not None:
            raise Exception(
                "Entry already has an incoming link {}".format(
                    self._incoming_link))
        self._incoming_processor = incoming_processor

    @property
    def defaultable(self):
        """ The defaultable status of the entry
        """
        if (self._incoming_link is None
                or self._incoming_processor is not None
                or len(self._out_going_links) != 1
                or self._out_going_processors):
            return False
        outgoing_link = next(iter(self._out_going_links))
        return (self._incoming_link + 3) % 6 == outgoing_link

    def merge_entry(self, other):
        """ Merges the another entry with this one and returns a new\
            MulticastRoutingTableByPartitionEntry

        :param other: \
            the MulticastRoutingTableByPartitionEntry to merge into this one
        :return: a merged MulticastRoutingTableByPartitionEntry
        """
        # pylint: disable=protected-access
        if not isinstance(other, MulticastRoutingTableByPartitionEntry):
            raise PacmanInvalidParameterException(
                "other", "type error",
                "The other parameter is not a instance of "
                "MulticastRoutingTableByPartitionEntry, and therefore cannot "
                "be merged.")
        # validate fixed things
        if (self._incoming_processor is None and
                other.incoming_processor is None):
            valid_incoming_processor = None
        elif (self._incoming_processor is not None and
                other._incoming_processor is None):
            valid_incoming_processor = self._incoming_processor
        elif (self._incoming_processor is None and
                other.incoming_processor is not None):
            valid_incoming_processor = other.incoming_processor
        elif self._incoming_processor == other._incoming_processor:
            valid_incoming_processor = self._incoming_processor
        else:
            raise PacmanInvalidParameterException(
                "incoming_processor", "invalid merge",
                "The two MulticastRoutingTableByPartitionEntry have "
                "different incoming_processors, and so can't be merged")

        if (self._incoming_link is None and
                other.incoming_link is None):
            valid_incoming_link = None
        elif (self._incoming_link is not None and
                other._incoming_link is None):
            valid_incoming_link = self._incoming_link
        elif (self._incoming_link is None and
                other.incoming_link is not None):
            valid_incoming_link = other.incoming_link
        elif self._incoming_link == other._incoming_link:
            valid_incoming_link = self._incoming_link
        else:
            raise PacmanInvalidParameterException(
                "incoming_link", "invalid merge",
                "The two MulticastRoutingTableByPartitionEntry have "
                "different incoming_links, and so can't be merged")

        # merge merge-able things
        merged_outgoing_processors = self._out_going_processors.union(
            other._out_going_processors)
        merged_outgoing_links = self._out_going_links.union(
            other._out_going_links)

        return MulticastRoutingTableByPartitionEntry(
            merged_outgoing_links, merged_outgoing_processors,
            valid_incoming_processor, valid_incoming_link)

    def __repr__(self):
        return "{}:{}:{}:{}:{}".format(
            self._incoming_link, self._incoming_processor,
            self.defaultable, self._out_going_links,
            self._out_going_processors)
