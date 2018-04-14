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
            self._out_going_links = set(int(link) for link in out_going_links)
        else:
            self._out_going_links = set()

        if isinstance(outgoing_processors, int):
            self._out_going_processors = set()
            self._out_going_processors.add(outgoing_processors)
        elif outgoing_processors is not None:
            self._out_going_processors = set(
                int(p) for p in outgoing_processors)
        else:
            self._out_going_processors = set()

        if incoming_link is not None and incoming_processor is not None:
            raise PacmanInvalidParameterException(
                "The incoming direction for a path can only be from either "
                "one link or one processors, not both",
                str(incoming_link), str(incoming_processor))
        if (incoming_processor is not None
                and not isinstance(incoming_processor, int)):
            raise PacmanInvalidParameterException(
                "The incoming direction for a path can only be from either "
                "one link or one processors, not both",
                str(incoming_link), str(incoming_processor))
        if incoming_link is not None and not isinstance(incoming_link, int):
            raise PacmanInvalidParameterException(
                "The incoming direction for a path can only be from either "
                "one link or one processors, not both",
                str(incoming_link), str(incoming_processor))
        self._incoming_processor = (
            None if incoming_processor is None else int(incoming_processor))
        self._incoming_link = (
            None if incoming_link is None else int(incoming_link))

    @property
    def out_going_processors(self):
        """ The destination processors of the entry

        :rtype: set(int)
        """
        return self._out_going_processors

    @property
    def out_going_links(self):
        """ The destination links of the entry

        :rtype: set(int)
        """
        return self._out_going_links

    @property
    def incoming_link(self):
        """ The source link for this path entry

        :rtype: int or None
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
        self._incoming_link = int(incoming_link)

    @property
    def incoming_processor(self):
        """ The source processor

        :rtype: int or Non
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
        self._incoming_processor = int(incoming_processor)

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

    @staticmethod
    def __merge_noneables(p1, p2, name):
        if p1 is None:
            return p2
        if p2 is None or p1 == p2:
            return p1
        raise PacmanInvalidParameterException(
            name, "invalid merge",
            "The two MulticastRoutingTableByPartitionEntry have different " +
            name + "s, and so can't be merged")

    def merge_entry(self, other):
        """ Merges the another entry with this one and returns a new\
            MulticastRoutingTableByPartitionEntry

        :param other: \
            the MulticastRoutingTableByPartitionEntry to merge into this one
        :return: a merged MulticastRoutingTableByPartitionEntry
        """
        if not isinstance(other, MulticastRoutingTableByPartitionEntry):
            raise PacmanInvalidParameterException(
                "other", "type error",
                "The other parameter is not an instance of "
                "MulticastRoutingTableByPartitionEntry, and therefore cannot "
                "be merged.")

        # validate and merge
        valid_incoming_processor = self.__merge_noneables(
            self._incoming_processor, other.incoming_processor,
            "incoming_processor")
        valid_incoming_link = self.__merge_noneables(
            self._incoming_link, other.incoming_link, "incoming_link")
        merged_outgoing_processors = self._out_going_processors.union(
            other.out_going_processors)
        merged_outgoing_links = self._out_going_links.union(
            other.out_going_links)

        return MulticastRoutingTableByPartitionEntry(
            merged_outgoing_links, merged_outgoing_processors,
            valid_incoming_processor, valid_incoming_link)

    def __repr__(self):
        return "{}:{}:{}:{{{}}}:{{{}}}".format(
            self._incoming_link, self._incoming_processor,
            self.defaultable,
            ", ".join(map(str, self._out_going_links)),
            ", ".join(map(str, self._out_going_processors)))
