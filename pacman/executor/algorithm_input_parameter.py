class AlgorithmInputParameter(object):
    """ An input parameter for an algorithm
    """

    __slots__ = [

        # The name of the input parameter
        "_name",

        # The type of the input parameter
        "_param_types"
    ]

    def __init__(self, name, param_types):
        """

        :param name: The name of the input parameter
        :type name: str
        :param param_types: The ordered possible types of the input parameter
        :type param_types: list of str
        """
        self._name = name
        self._param_type = type

    @property
    def name(self):
        """ The name of the input parameter
        """
        return self._name

    @property
    def param_type(self):
        """ The type of the parameter
        """
        return self._param_type
