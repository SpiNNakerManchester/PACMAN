class MulticastRoute(object):
    """ Represents a multicast route, consisting of the destination links and\
        processors on a chip
    """
    
    def __init__(self, processor_ids, link_ids):
        """
        
        :param processor_ids: An iterable of processor ids
        :type processor_ids: iterable of int
        :param link_ids: An iterable of link ids
        :type link_ids: iterable of int
        :raise None: No known exceptions are raised
        """
        pass
    
    @property
    def processor_ids(self):
        """ The ids of the destination processors on a chip
        
        :return: An iterable of processor ids
        :rtype: iterable of int
        """
        pass
    
    @property
    def link_ids(self):
        """ The ids of the destination links from a chip
        
        :return: An iterable of link ids
        :rtype: iterable of int
        """
        pass
