__author__ = 'daviess'


class Router(object):
    """ Creates a new router object with a number of available links"""

    def __init__(self, links=None):
        """

        :param links: list of available links (from 0 to 5 following\
                      SpiNNaker datasheet) or None
        :type links: None or list of int
        :return: a router object
        :rtype: pacman.machine.chip.Router
        :raise None: does not raise any known exceptions
        """
        pass

    def add_link(self, link):
        """
        Adds a link to router's available links

        :param link: the link to add
        :type link: int
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        pass

    def add_links(self, links):
        """
        Adds a set of links to router's available links

        :param link: the set of links to add
        :type link: list of int
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        pass

    def del_link(self, link):
        """
        Removes a link from router's available links

        :param link: the link to remove
        :type link: int
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        pass

    def del_links(self, links):
        """
        Removes a set of links from router's available links

        :param link: the set of links to remove
        :type link: list of int
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def links(self):
        """
        Returns the available links of this router

        :return: the set of available links
        :rtype: list of int
        :raise None: does not raise any known exceptions
        """
        pass

