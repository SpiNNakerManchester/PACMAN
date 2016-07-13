from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty


@add_metaclass(ABCMeta)
class AbstractInput(object):
    """ An abstract input to an algorithm
    """

    @abstractproperty
    def name(self):
        """ The name of the input
        """

    @abstractproperty
    def param_types(self):
        """ The types of the input
        """

    @abstractmethod
    def get_inputs_by_name(self, inputs):
        """ Get the inputs that match this input by parameter name

        :param inputs: A dict of type to value
        :return: A dict of parameter name to value
        :rtype: dict
        """

    @abstractmethod
    def input_matches(self, inputs):
        """ Determine if this input is in the set of inputs

        :param inputs: A set of input types
        :return: True if this input type is in the list
        """
