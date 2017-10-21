class ElementFreeSpace(object):

    def __init__(self, start_address, size):
        self._start_address = start_address
        self._size = size

    @property
    def start_address(self):
        return self._start_address

    @property
    def size(self):
        return self._size

    def __repr__(self):
        return "ElementFreeSpace:start={}:size={}".format(
            hex(self._start_address), self._size)

    def __str__(self):
        return self.__repr__()
