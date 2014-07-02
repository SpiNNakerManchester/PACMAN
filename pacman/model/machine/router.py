from collections import OrderedDict
from pacman.exceptions import PacmanAlreadyExistsException

class Router(object):
    """ Represents a router of a chip, with a set of available links
    """
    
    def __init__(self, links):
        """

        :param links: iterable of links
        :type links: iterable of :py:class:`pacman.model.machine.link.Link`
        :raise pacman.exceptions.PacmanAlreadyExistsException: If any two links\
                    have the same source_link_id
        """
        self._links = OrderedDict()
        for link in sorted(links, key=lambda x: x.source_link_id):
            if link.source_link_id in self._links:
                raise PacmanAlreadyExistsException("link", link.source_link_id)
            self._links[link.source_link_id] = link
            
    def is_link(self, source_link_id):
        """ Determine if there is a link with id source_link_id
        
        :param source_link_id: The id of the link to find
        :type source_link_id: int
        :return: True if there is a link with the given id, False otherwise
        :rtype: bool
        :raise None: No known exceptions are raised
        """
        return source_link_id in self._links
    
    def get_link(self, source_link_id):
        """ Get the link with the given id, or None if no such link
        
        :param source_link_id: The id of the link to find
        :type source_link_id: int
        :return: The link, or None if no such link
        :rtype: :py:class:`pacman.model.machine.link.Link`
        :raise None: No known exceptions are raised
        """
        if source_link_id in self._links:
            return self._links[source_link_id]
        return None
        
    @property
    def links(self):
        """ The available links of this router

        :return: an iterable of available links
        :rtype: iterable of :py:class:`pacman.model.machine.link.Link`
        :raise None: does not raise any known exceptions
        """
        return self._links.itervalues()
