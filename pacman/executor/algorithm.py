_algorithm_data = dict()


def algorithm_class(algorithm_class):
    """ Describe the algorithm implemented by this class

    :param required_inputs:\
        A dict of name of parameter -> type of the required arguments
    :param optional_inputs:\
        A dict of name of parameter -> type of the optional arguments
    :param outputs:\
        An ordered list of types that will be returned, with the order\
        matching the order of the returned items
    """

    def wrap(required_inputs, optional_inputs, outputs, name=None):

        # Work out the name of the algorithm
        algorithm_name = name
        if name is None:
            algorithm_name = algorithm_class.__name__

        # Get the algorithm module
        algorithm_module = algorithm_class.__module__
