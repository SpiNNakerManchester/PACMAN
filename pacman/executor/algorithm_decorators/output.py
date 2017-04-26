class Output(object):
    """ Represents an output from an algorithm
    """

    __slots__ = [
        # The type of the output
        "_output_type",
        # The name of the type holding the file name
        "_file_name_type"
    ]

    def __init__(self, output_type, file_name_type=None):
        """

        :param output_type: The type of the output
        :param file_name_type:\
            If the output is file based, the type of the input holding\
            the file name
        """
        self._output_type = output_type
        self._file_name_type = file_name_type

    @property
    def output_type(self):
        return self._output_type

    @property
    def file_name_type(self):
        return self._file_name_type

    def __repr__(self):
        return "Output(output_type={}, file_name_type={})".format(
            self._output_type, self._file_name_type)
