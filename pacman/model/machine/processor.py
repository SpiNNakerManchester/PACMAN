class Processor(object):
    """ A processor object included in a chip 
    """

    def __init__(self, processor_id):
        """

        :param processor_id: id of the processor in the chip
        :type processor_id: int
        :raise None: does not raise any known exceptions
        """
        self._processor_id = processor_id

    @property
    def processor_id(self):
        """ The id of the processor

        :return: id of the processor
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._processor_id
