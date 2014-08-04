class PacmanException(Exception):
    """ Indicates a general exception from Pacman
    """
    pass


class PacmanInvalidParameterException(PacmanException):
    """ An exception which indicates that a parameter has an invalid value
    """
    
    def __init__(self, parameter, value, problem):
        """
        
        :param parameter: The name of the parameter
        :type parameter: str
        :param value: The value of the parameter
        :type value: str
        :param problem: The problem with the value of the parameter
        :type problem: str
        """
        pass


class PacmanAlreadyExistsException(PacmanException):
    """ An exception that indicates that something already exists and that
        adding another would be a conflict
    """
    
    def __init__(self, item_type, item_id):
        """
        
        :param item_type: The type of the item that already exists
        :type item_type: str
        :param item_id: The id of the item which is in conflict
        :type item_id: str
        """
        pass


class PacmanPartitionException(PacmanException):
    """ An exception that indicates that something went wrong with paritioning
    """
    
    def __init__(self, problem):
        """
        :param problem: The problem with the partitioning
        :type problem: str
        """
        pass


class PacmanPlaceException(PacmanException):
    """ An exception that indicates that something went wrong with placement
    """
    
    def __init__(self, problem):
        """
        :param problem: The problem with the placement
        :type problem: str
        """
        pass


class PacmanPruneException(PacmanException):
    """ An exception that indicates that something went wrong with pruning
    """
    
    def __init__(self, problem):
        """
        :param problem: The problem with the pruning
        :type problem: str
        """
        pass


class PacmanRouteInfoAllocationException(PacmanException):
    """ An exception that indicates that something went wrong with route info\
        allocation
    """
    
    def __init__(self, problem):
        """
        :param problem: The problem with the allocation
        :type problem: str
        """
        pass


class PacmanRoutingException(PacmanException):
    """ An exception that indicates that something went wrong with routing
    """
    
    def __init__(self, problem):
        """
        :param problem: The problem with the routing
        :type problem: str
        """
        pass


class PacmanConfigurationException(PacmanException):
    """ An exception that indicates that something went wrong with \
    configuring some part of pacman
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the routing
        :type problem: str
        """
        pass