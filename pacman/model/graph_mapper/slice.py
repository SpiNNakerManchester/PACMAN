class Slice(object):

    def __init__(self, lo_atom, hi_atom):
        self._lo_atom = lo_atom
        self._hi_atom = hi_atom

    @property
    def lo_atom(self):
        return self._lo_atom

    @property
    def hi_atom(self):
        return self._hi_atom

    @property
    def n_atoms(self):
        return (self._hi_atom - self.lo_atom) + 1

    def __str__(self):
        return "slice with atoms {} to {}".format(self._lo_atom, self._hi_atom)

    def __repr__(self):
        return self.__str__()