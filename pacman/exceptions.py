class PacmanException(Exception):
    """ Indicates a general exception from Pacman
    """
    def __init__(self, *args, **kwargs):

        # Call the base class constructor with the parameters it needs
        Exception.__init__(self, *args, **kwargs)


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
        PacmanException.__init__(self, parameter, value, problem)


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
        PacmanException.__init__(self, item_type, item_id)


class PacmanPartitionException(PacmanException):
    """ An exception that indicates that something went wrong with partitioning
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the partitioning
        :type problem: str
        """
        PacmanException.__init__(self, problem)


class PacmanPlaceException(PacmanException):
    """ An exception that indicates that something went wrong with placement
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the placement
        :type problem: str
        """
        PacmanException.__init__(self, problem)


class PacmanPruneException(PacmanException):
    """ An exception that indicates that something went wrong with pruning
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the pruning
        :type problem: str
        """
        PacmanException.__init__(self, problem)


class PacmanRouteInfoAllocationException(PacmanException):
    """ An exception that indicates that something went wrong with route info\
        allocation
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the allocation
        :type problem: str
        """
        PacmanException.__init__(self, problem)


class PacmanElementAllocationException(PacmanException):
    """ An exception that indicates that something went wrong with element\
        allocation
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the allocation
        :type problem: str
        """
        PacmanException.__init__(self, problem)


class PacmanRoutingException(PacmanException):
    """ An exception that indicates that something went wrong with routing
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the routing
        :type problem: str
        """
        PacmanException.__init__(self, problem)


class PacmanConfigurationException(PacmanException):
    """ An exception that indicates that something went wrong with \
        configuring some part of pacman
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the routing
        :type problem: str
        """
        PacmanException.__init__(self, problem)


class PacmanNotExistException(PacmanException):
    """ An exception that indicates that a routing table entry was attempted\
        to be removed from a routing table which didn't have such an entry

    """

    def __init__(self, problem):
        """
        :param problem: The problem with the routing
        :type problem: str
        """
        PacmanException.__init__(self, problem)


class PacmanAlgorithmFailedToCompleteException(PacmanException):
    """ An exception that indicates that a pacman algorithm ran from outside\
        the software stack has failed to complete for some unknown reason.

    """

    def __init__(self, problem):
        """
        :param problem: The problem with the routing
        :type problem: str
        """
        PacmanException.__init__(self, problem)


class PacmanSubvertexAlreadyPlacedError(ValueError):
    """Indicates multiple placements are being made for a subvertex."""
    pass


class PacmanSubvertexNotPlacedError(KeyError):
    """Indicates no placements are made for a subvertex."""
    pass


class PacmanProcessorAlreadyOccupiedError(ValueError):
    """Indicates multiple placements are being made to a processor."""
    pass


class PacmanProcessorNotOccupiedError(KeyError):
    """Indicates that no placement has been made to a processor."""
    pass


class PacmanValueError(ValueError, PacmanException):
    """Indicates that a value is invalid for some reason."""
    pass


class PacmanNotFoundError(KeyError, PacmanException):
    """Indicates that some object has not been found when requested."""
    pass


class PacmanTypeError(TypeError, PacmanException):
    """Indicates that an object is of incorrect type."""
    pass
