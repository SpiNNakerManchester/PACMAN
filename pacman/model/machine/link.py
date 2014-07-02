class Link(object):
    """ Represents a directional link between chips in the machine
    """
    
    def __init__(self, source_x, source_y, source_link_id, destination_x, 
            destination_y, multicast_default_from, multicast_default_to):
        """
        
        :param source_x: The x-coordinate of the source chip of the link
        :type source_x: int
        :param source_y: The y-coordinate of the source chip of the link
        :type source_y: int
        :param source_link_id: The id of the link in the source chip
        :type source_link_id: int
        :param destination_x: The x-coordinate of the destination chip of the\
                    link
        :type destination_x: int
        :param destination_y: The y-coordinate of the destination chip of the\
                    link
        :type destination_y: int
        :param multicast_default_from: The id of the link in the source chip\
                    such that multicast traffic received from that link will\
                    default to this link if no routing entry exists, or None
                    if this link is not the default for any link
        :type multicast_default_from: int
        :param multicast_default_to: The id of the link in the source chip\
                    such that multicast traffic received on this link will\
                    default to that link if no routing entry exists, or None
                    if there is no such default link
        """
        pass
    
    @property
    def source_x(self):
        """ The x-coordinate of the source chip of this link
        
        :return: The x-coordinate
        :rtype: int
        """
        pass
    
    @property
    def source_y(self):
        """ The y-coordinate of the source chip of this link
        
        :return: The y-coordinate
        :rtype: int
        """
        pass
    
    @property
    def source_link_id(self):
        """ The id of the link on the source chip
        
        :return: The link id
        :rtype: int
        """
        pass
    
    @property
    def destination_x(self):
        """ The x-coordinate of the destination chip of this link
        
        :return: The x-coordinate
        :rtype: int
        """
        pass
    
    @property
    def destination_y(self):
        """ The y-coordinate of the destination chip of this link
        
        :return: The y-coordinate
        :rtype: int
        """
        pass
    
    @property
    def multicast_default_from(self):
        """ The id of the link for which this link is the default
        
        :return: The id of a link, or None if no such link
        :rtype: int
        """
        pass
    
    @property
    def multicast_default_to(self):
        """ The id of the link to which to send default routed multicast
        
        :return: The id of a link, or None if no such link
        :rtype: int
        """
        pass
