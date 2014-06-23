__author__ = 'daviess'


class Router(object):
    """ Creates a new router object with a list of available links"""

    def __init__(self, links=None):
        """

        :param links: list of 6 elements each set to 1 or 0 depending if the\
        link is functional or not. In alternative None if no links are specified
        :type links: list of int or None
        :return: a router object
        :rtype: pacman.machine.chip.Router
        :raise None: does not raise any known exceptions
        """
        if links is None or links.__len__() != 6:
            self._links = [0 for i in xrange(6)]
        else:
            self._links = links

    def add_link(self, link):
        """
        Adds a link to router's available links

        :param link: the link to add
        :type link: int
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        self._links[link] = 1

    def del_link(self, link):
        """
        Removes a link from router's available links

        :param link: the link to remove
        :type link: int
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        self._links[link] = 0

    def set_links(self, links):
        """
        Adds a set of links to router's available links

        :param link: list of 6 elements each set to 1 or 0 depending if the\
        link is functional or not.
        :type link: list of int
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        if links is not None and links.__len__() == 6:
            self._links = links

    @property
    def links(self):
        """
        Returns the available links of this router

        :return: the set of available links
        :rtype: list of int
        :raise None: does not raise any known exceptions
        """
        return self._links

