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

    def __repr__(self):
        return "Token(name={}, part={})".format(self._name, self._part)

    def __hash__(self):
        return ((self._name, self._part)).__hash__()

    def __eq__(self, other):
        if not isinstance(other, Token):
            return False
        return self._name == other.name and self._part == other.part
