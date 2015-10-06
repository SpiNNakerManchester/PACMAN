"""
AlgorithmData
"""


class AlgorithmData(object):
    """
    data object for reading in xml and locations
    """

    def __init__(self, algorithm_id, command_line_args, python_import, inputs,
                 optional_inputs, outputs, external, python_class,
                 python_function):
        """

        :param algorithm_id:
        :param command_line_args:
        :param inputs:
        :param optional_inputs:
        :param outputs:
        :param external:
        :return:
        """
        self._id = algorithm_id
        self._command_line_args = command_line_args
        self._python_import_string = python_import
        self._inputs = inputs
        self._optional_inputs = optional_inputs
        self._outputs = outputs
        self._external = external
        self._python_class = python_class
        self._python_function = python_function

    @property
    def algorithm_id(self):
        """
        the id for this algorituhm
        :return:
        """
        return self._id

    @property
    def python_class(self):
        """
        returns the python class if it has one
        :return:
        """
        return self._python_class

    @property
    def python_function(self):
        """
        returns the python function if it has one
        :return:
        """
        return self._python_function

    @property
    def inputs(self):
        """
        the dict of inputs and type
        :return:
        """
        return self._inputs

    @property
    def outputs(self):
        """
        the dict of outputs and type
        :return:
        """
        return self._outputs

    @property
    def optional_inputs(self):
        """
        the dict of optional inputs and type
        :return:
        """
        return self._optional_inputs

    @property
    def command_line_args(self):
        """
        the string which is to be the command line to call if external call
        :return:
        """
        return self._command_line_args

    @property
    def external(self):
        """
        bool that says if this
        :return:
        """
        return self._external

    @property
    def python_module_import(self):
        """
        the string for how to import this module
        :return:
        """
        return self._python_import_string

    def get_type_from_output_name(self, name):
        """
        locates the type from a output name
        :param name: the name to find the type of
        :return: the tpye of the param
        """
        for output in self._outputs:
            if output['name'] == name:
                return output['type']
        else:
            return None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "{}:{}:{}:{}:{}:{}:{}:{}:{}".format(
            self._id, self._command_line_args, self._python_import_string,
            self._inputs, self._optional_inputs, self._outputs, self._external,
            self._python_class, self._python_function)
