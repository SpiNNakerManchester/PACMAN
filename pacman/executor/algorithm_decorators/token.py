class Token(object):
    """ A token in the algorithm flow that indicates a process or part of a\
        process
    """

    __slots__ = [

        # The name of the token
        "_name",

        # The part of the token, or None if no part
        "_part"
    ]

    def __init__(self, name, part=None):
        self._name = name
        self._part = part

    @property
    def name(self):
        return self._name

    @property
    def part(self):
        return self._part
