

class MultiCastNoPayloadPacketsPerTic(object):

    def __init__(self, rate):
        self._rate = rate

    @property
    def rate(self):
        return self._rate

    def __repr__(self):
        return "MultiCastNoPayloadPacketsPerTic:rate={}".format(self._rate)

    def __str__(self):
        return self.__repr__()
